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

app = Flask(__name__)
@app.route('/')
def health_check():
    return "Bot is Verified & Optimized!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

db_client = MongoClient(Config.MONGO_URI)
db = db_client[Config.DB_NAME]
user_data = db.users

bot = Client("VideoBot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

# --- ভেরিফিকেশন লজিক ---
async def is_verified(user_id):
    if not Config.SHORTENER_ON:
        return True
    user = user_data.find_one({"user_id": user_id})
    if user and (time.time() - user.get("last_verify", 0) < Config.VERIFY_EXPIRE):
        return True
    return False

def get_verify_link(user_id):
    bot_url = f"https://t.me/{(bot.get_me()).username}?start=verify_{user_id}"
    api_url = f"https://{Config.SHORTENER_URL}/api?api={Config.SHORTENER_API}&url={bot_url}"
    res = requests.get(api_url).json()
    return res.get("shortenedUrl", bot_url)

# --- ভিডিও ফেচিং (বন্ধুর ফিক্সসহ) ---
async def get_videos(user_id, category):
    actual_category = random.choice(list(Config.CHANNELS.keys())) if category == "random" else category
    channel_id = Config.CHANNELS.get(actual_category)
    user = user_data.find_one({"user_id": user_id}) or {}
    seen_ids = user.get(f"seen_{actual_category}", [])

    videos = []
    [span_6](start_span)async for message in bot.get_chat_history(channel_id, limit=200): # CPU Fix[span_6](end_span)
        if message.video or (message.document and "video" in message.document.mime_type):
            if message.id not in seen_ids:
                videos.append(message.id)
            if len(videos) >= 10: break
    
    if videos:
        [span_7](start_span)user_data.update_one({"user_id": user_id}, {"$push": {f"seen_{actual_category}": {"$each": videos, "$slice": -500}}}, upsert=True) # DB Fix[span_7](end_span)
    return videos, channel_id

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    user_id = message.from_user.id
    
    # ভেরিফিকেশন চেক (লিঙ্ক ক্লিক করে ফিরে আসলে)
    if len(message.command) > 1 and message.command[1].startswith("verify_"):
        user_data.update_one({"user_id": user_id}, {"$set": {"last_verify": time.time()}}, upsert=True)
        return await message.reply("✅ আপনার ভেরিফিকেশন সফল হয়েছে! এখন আপনি ২৪ ঘণ্টা ভিডিও দেখতে পারবেন।")

    # ফোর্স সাবস্ক্রাইব
    try:
        await client.get_chat_member(Config.FSUB_CHANNEL, user_id)
    except:
        return await message.reply("আগে জয়েন করুন!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=Config.FSUB_LINK)]]))

    buttons = [
        [InlineKeyboardButton("Indian 🇮🇳", callback_data="vid_indian"), InlineKeyboardButton("English 🇺🇸", callback_data="vid_english")],
        [InlineKeyboardButton("OnlyFan 🔥", callback_data="vid_onlyfan"), InlineKeyboardButton("Japanese 🇯🇵", callback_data="vid_japanese")],
        [InlineKeyboardButton("Viral Videos 🚀", callback_data="vid_viral")],
        [InlineKeyboardButton("Random Videos 🎲", callback_data="vid_random")]
    ]
    await message.reply("ক্যাটাগরি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("^vid_"))
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    
    # [span_8](start_span)ভেরিফিকেশন চেক (দিনে একবার)[span_8](end_span)
    if not await is_verified(user_id):
        v_link = get_verify_link(user_id)
        return await callback_query.message.reply("🚫 আপনার ভেরিফিকেশন শেষ। ২৪ ঘণ্টার এক্সেস পেতে নিচের লিঙ্কে ক্লিক করে ভেরিফাই করুন।", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Verify Now (24h)", url=v_link)]]))

    await callback_query.answer("ভিডিও পাঠানো হচ্ছে...")
    try:
        video_ids, ch_id = await get_videos(user_id, callback_query.data.split("_")[1])
        if not video_ids: return await callback_query.message.reply("নতুন ভিডিও নেই!")
        for v_id in video_ids:
            await bot.copy_message(chat_id=user_id, from_chat_id=ch_id, message_id=v_id)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run()
