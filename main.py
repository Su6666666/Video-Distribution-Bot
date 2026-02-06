import os
import time
import random
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from flask import Flask
from threading import Thread
from config import Config

# Flask Web Server for Render & Koyeb Health Check
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is Running Successfully!"

def run_web():
    # Render ও Koyeb উভয়ের জন্য পোর্ট হ্যান্ডেলিং
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Database Connection
db_client = MongoClient(Config.MONGO_URI)
db = db_client[Config.DB_NAME]
user_data = db.users

# Telegram Client
bot = Client(
    "VideoBot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

# --- Verification Logic ---
async def is_verified(user_id):
    if not Config.SHORTENER_ON:
        return True
    user = user_data.find_one({"user_id": user_id})
    if user and (time.time() - user.get("last_verify", 0) < Config.VERIFY_EXPIRE):
        return True
    return False

async def get_verify_link(user_id):
    me = await bot.get_me()
    bot_url = f"https://t.me/{me.username}?start=verify_{user_id}"
    api_url = f"https://{Config.SHORTENER_URL}/api?api={Config.SHORTENER_API}&url={bot_url}"
    try:
        res = requests.get(api_url).json()
        return res.get("shortenedUrl", bot_url)
    except:
        return bot_url

# --- Video Fetching Logic ---
async def get_videos(user_id, category):
    actual_category = random.choice(list(Config.CHANNELS.keys())) if category == "random" else category
    channel_id = Config.CHANNELS.get(actual_category)
    
    user = user_data.find_one({"user_id": user_id}) or {}
    seen_ids = user.get(f"seen_{actual_category}", [])

    videos = []
    # ২শ মেসেজ স্ক্যান করা হবে যাতে নতুন ভিডিও পাওয়া যায়
    async for message in bot.get_chat_history(channel_id, limit=200):
        if message.video or (message.document and "video" in message.document.mime_type):
            if message.id not in seen_ids:
                videos.append(message.id)
            if len(videos) >= 10: break # প্রতিবার সর্বোচ্চ ১০টি ভিডিও
    
    if videos:
        # ডেটাবেসে দেখা ভিডিওর আইডি সেভ করা (সর্বোচ্চ ৫০০টি পর্যন্ত)
        user_data.update_one(
            {"user_id": user_id}, 
            {"$push": {f"seen_{actual_category}": {"$each": videos, "$slice": -500}}}, 
            upsert=True
        )
    return videos, channel_id

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    user_id = message.from_user.id
    
    # Verification Callback
    if len(message.command) > 1 and message.command[1].startswith("verify_"):
        user_data.update_one({"user_id": user_id}, {"$set": {"last_verify": time.time()}}, upsert=True)
        return await message.reply("✅ আপনার ভেরিফিকেশন সফল! এখন আপনি ২৪ ঘণ্টা ভিডিও দেখতে পারবেন।")

    # Force Subscribe Check
    try:
        await client.get_chat_member(Config.FSUB_CHANNEL, user_id)
    except:
        return await message.reply(
            "বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন।", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=Config.FSUB_LINK)]])
        )

    buttons = [
        [InlineKeyboardButton("Indian 🇮🇳", callback_data="vid_indian"), InlineKeyboardButton("English 🇺🇸", callback_data="vid_english")],
        [InlineKeyboardButton("OnlyFan 🔥", callback_data="vid_onlyfan"), InlineKeyboardButton("Japanese 🇯🇵", callback_data="vid_japanese")],
        [InlineKeyboardButton("Viral Videos 🚀", callback_data="vid_viral")],
        [InlineKeyboardButton("Random Videos 🎲", callback_data="vid_random")]
    ]
    await message.reply("নিচের ক্যাটাগরি থেকে আপনার পছন্দের ভিডিও সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("^vid_"))
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    
    if not await is_verified(user_id):
        v_link = await get_verify_link(user_id)
        return await callback_query.message.reply(
            "🚫 আপনার ভেরিফিকেশন শেষ। ২৪ ঘণ্টার এক্সেস পেতে নিচের লিঙ্কে ক্লিক করে ভেরিফাই করুন।", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Verify Now (24h)", url=v_link)]])
        )

    await callback_query.answer("ভিডিও খোঁজা হচ্ছে...")
    try:
        video_ids, ch_id = await get_videos(user_id, callback_query.data.split("_")[1])
        if not video_ids: 
            return await callback_query.message.reply("নতুন কোনো ভিডিও পাওয়া যায়নি। অনুগ্রহ করে কিছুক্ষণ পর চেষ্টা করুন।")
        
        for v_id in video_ids:
            await bot.copy_message(chat_id=user_id, from_chat_id=ch_id, message_id=v_id)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # ওয়েব সার্ভার আলাদা থ্রেডে চালানো হচ্ছে
    Thread(target=run_web).start()
    bot.run()
