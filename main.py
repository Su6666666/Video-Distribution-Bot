import os
import random
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from flask import Flask
from threading import Thread
from config import Config

# --- Koyeb Health Check Web Server ---
app = Flask(__name__)
@app.route('/')
def health_check():
    return "Bot is Alive and Running!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- Database Setup ---
db_client = MongoClient(Config.MONGO_URI)
db = db_client[Config.DB_NAME]
user_data = db.users

bot = Client("VideoBot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# --- Link Shortener Logic ---
def get_shortlink(url):
    if not Config.SHORTENER_ON or not Config.SHORTENER_API:
        return url
    try:
        api_url = f"https://{Config.SHORTENER_URL}/api?api={Config.SHORTENER_API}&url={url}"
        res = requests.get(api_url)
        data = res.json()
        return data.get("shortenedUrl", url)
    except:
        return url

# --- Video Fetching Logic ---
async def get_videos(user_id, category):
    if category == "random":
        actual_category = random.choice(list(Config.CHANNELS.keys()))
    else:
        actual_category = category

    channel_id = Config.CHANNELS.get(actual_category)
    user = user_data.find_one({"user_id": user_id}) or {}
    seen_ids = user.get(f"seen_{actual_category}", [])

    videos = []
    # get_chat_history ডিফল্টভাবে নতুন মেসেজ আগে দেয় (নিচ থেকে শুরু হবে)
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

# --- Command Handlers ---
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    # Force Subscribe Check
    try:
        await client.get_chat_member(Config.FSUB_CHANNEL, message.from_user.id)
    except:
        return await message.reply(
            "বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url="https://t.me/StreamAlertsIndia")]])
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
    video_ids, ch_id = await get_videos(user_id, category)

    if not video_ids:
        return await callback_query.message.reply("আপনার জন্য কোনো নতুন ভিডিও নেই! পরে চেষ্টা করুন।")

    for v_id in video_ids:
        try:
            # ভিডিও কপি করে পাঠানো
            await bot.copy_message(chat_id=user_id, from_chat_id=ch_id, message_id=v_id)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Koyeb পোর্টের জন্য আলাদা থ্রেড
    Thread(target=run_web).start()
    bot.run()
