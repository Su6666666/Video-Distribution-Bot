import os
import random
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from flask import Flask
from threading import Thread
from config import Config

# --- Koyeb Health Check ---
app = Flask(__name__)
@app.route('/')
def health_check():
    return "Bot is Optimized and Running!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- Database ---
db_client = MongoClient(Config.MONGO_URI)
db = db_client[Config.DB_NAME]
user_data = db.users

bot = Client("VideoBot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# --- Video Fetching Logic (Fixed) ---
async def get_videos(user_id, category):
    if category == "random":
        actual_category = random.choice(list(Config.CHANNELS.keys()))
    else:
        actual_category = category

    channel_id = Config.CHANNELS.get(actual_category)
    user = user_data.find_one({"user_id": user_id}) or {}
    seen_ids = user.get(f"seen_{actual_category}", [])

    videos = []
    # FIX 2: limit=200 যোগ করা হয়েছে যাতে CPU/API রিস্ক না থাকে
    async for message in bot.get_chat_history(channel_id, limit=200):
        if message.video or (message.document and "video" in message.document.mime_type):
            if message.id not in seen_ids:
                videos.append(message.id)
            if len(videos) >= 10:
                break
    
    if videos:
        # FIX 1: $slice: -500 যোগ করা হয়েছে যাতে DB সাইজ কন্ট্রোলে থাকে
        user_data.update_one(
            {"user_id": user_id}, 
            {
                "$push": {
                    f"seen_{actual_category}": {
                        "$each": videos,
                        "$slice": -500 
                    }
                }
            }, 
            upsert=True
        )
    return videos, channel_id

# --- Command Handlers ---
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    try:
        await client.get_chat_member(Config.FSUB_CHANNEL, message.from_user.id)
    except:
        # FIX 5: Config থেকে ডায়নামিক লিঙ্ক ব্যবহার করা হয়েছে
        return await message.reply(
            "বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=Config.FSUB_LINK)]])
        )

    buttons = [
        [InlineKeyboardButton("Indian 🇮🇳", callback_data="vid_indian"), InlineKeyboardButton("English 🇺🇸", callback_data="vid_english")],
        [InlineKeyboardButton("OnlyFan 🔥", callback_data="vid_onlyfan"), InlineKeyboardButton("Japanese 🇯🇵", callback_data="vid_japanese")],
        [InlineKeyboardButton("Viral Videos 🚀", callback_data="vid_viral")],
        [InlineKeyboardButton("Random Videos 🎲", callback_data="vid_random")]
    ]
    await message.reply("নিচের একটি অপশন সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("^vid_"))
async def handle_callback(client, callback_query):
    category = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    
    await callback_query.answer("ভিডিও সংগ্রহ করা হচ্ছে...")
    
    try:
        video_ids, ch_id = await get_videos(user_id, category)

        if not video_ids:
            return await callback_query.message.reply("নতুন কোনো ভিডিও নেই! পরে চেষ্টা করুন।")

        for v_id in video_ids:
            try:
                await bot.copy_message(chat_id=user_id, from_chat_id=ch_id, message_id=v_id)
            except Exception as e:
                print(f"Send Error: {e}")
                
    except Exception as e:
        # FIX 6: ইউজার সাইড এরর হ্যান্ডলিং
        await callback_query.message.reply("দুঃখিত, কোনো একটি সমস্যা হয়েছে। আবার চেষ্টা করুন।")
        print(f"Main Error: {e}")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run()
