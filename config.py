import os

class Config:
    # Telegram API Details
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # Database Details
    MONGO_URI = os.environ.get("MONGO_URI", "")
    DB_NAME = os.environ.get("DB_NAME", "VideoBot")
    
    # Force Subscribe Details
    FSUB_CHANNEL = int(os.environ.get("FSUB_CHANNEL", "-100")) 
    FSUB_LINK = os.environ.get("FSUB_LINK", "https://t.me/StreamAlertsIndia")
    
    # Video Channels
    CHANNELS = {
        "indian": int(os.environ.get("INDIAN_CH", "-100")),
        "english": int(os.environ.get("ENGLISH_CH", "-100")),
        "onlyfan": int(os.environ.get("ONLYFAN_CH", "-100")),
        "japanese": int(os.environ.get("JAPANESE_CH", "-100")),
        "viral": int(os.environ.get("VIRAL_CH", "-100"))
    }
    
    # Link Shortener Settings
    SHORTENER_URL = os.environ.get("SHORTENER_URL", "")
    SHORTENER_API = os.environ.get("SHORTENER_API", "")
    SHORTENER_ON = os.environ.get("SHORTENER_ON", "False").lower() == "true"
    VERIFY_EXPIRE = 86400 # 24 Hours
