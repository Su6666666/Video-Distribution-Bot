import os
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from flask import Flask
from threading import Thread
from config import Config

# Koyeb Health Check Web Server
app = Flask(__name__)
@app.route('/')
def health_check():
    return "Bot is Running Perfectly!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# MongoDB Setup
db_client = MongoClient(Config.MONGO_URI)
db = db_client[Config.DB_NAME]
user_data = db.users

bot = Client("VideoBot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

async def get_videos(user_id, category):
    # Random selection logic
    if category == "random":
        actual_category = random.choice(list(Config.CHANNELS.keys()))
    else:
        actual_category = category

    channel_id = Config.CHANNELS.get(actual_category)
    user = user_data.find_one({"user_id": user_id}) or {}
    seen_ids = user.get(f"seen_{actual_category}", [])

    videos = []
    # Fetching Newest to Oldest (নিচ থেকে শুরু)
    async for message in bot.get_chat_history(channel_id):
        if message.video or (message.document and "video" in message.document.mime_type):
            if message.id not in seen_ids:
                videos.append(message.id)
            if len(videos) >= 10: # সর্বোচ্চ ১০টি ভিডিও
                break
    
    if videos:
        user_data.update_one(
            {"user_id": user_id}, 
            {"$push": {f"seen_{actual_category}": {"$each": videos}}}, 
            upsert=True
        )
    return videos, channel_id

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    # Force Subscribe Logic
    try:
        await client.get_chat_member(Config.FSUB_CHANNEL, message.from_user.id)
    except:
        return await message.reply(
            "বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Now", url="https://t.me/StreamAlertsIndia")]])
        )

    buttons = [
        [InlineKeyboardButton("Indian 🇮🇳", callback_data="vid_indian"), InlineKeyboardButton("English 🇺🇸", callback_data="vid_english")],
        [InlineKeyboardButton("OnlyFan 🔥", callback_data="vid_onlyfan"), InlineKeyboardButton("Japanese 🇯🇵", callback_data="vid_japanese")],
        [InlineKeyboardButton("Viral Videos 🚀", callback_data="vid_viral")],
        [InlineKeyboardButton("Random Videos 🎲", callback_data="vid_random")]
    ]
    await message.reply("ক্যাটাগরি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("^vid_"))
async def handle_callback(client, callback_query):
    category = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    
    await callback_query.answer("ভিডিও সংগ্রহ করা হচ্ছে...")
    video_ids, ch_id = await get_videos(user_id, category)

    if not video_ids:
        return await callback_query.message.reply("আপনার জন্য কোনো নতুন ভিডিও নেই!")

    for v_id in video_ids:
        try:
            await bot.copy_message(chat_id=user_id, from_chat_id=ch_id, message_id=v_id)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run()
