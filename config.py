import os

class Config:
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    MONGO_URI = os.environ.get("MONGO_URI", "")
    DB_NAME = os.environ.get("DB_NAME", "VideoBot")
    FSUB_CHANNEL = int(os.environ.get("FSUB_CHANNEL", "-100")) 
    FSUB_LINK = os.environ.get("FSUB_LINK", "https://t.me/StreamAlertsIndia")
    
    CHANNELS = {
        "indian": int(os.environ.get("INDIAN_CH", "-100")),
        "english": int(os.environ.get("ENGLISH_CH", "-100")),
        "onlyfan": int(os.environ.get("ONLYFAN_CH", "-100")),
        "japanese": int(os.environ.get("JAPANESE_CH", "-100")),
        "viral": int(os.environ.get("VIRAL_CH", "-100"))
    }
    
    # শর্টনার ও ভেরিফাই সেটিংস
    SHORTENER_URL = os.environ.get("SHORTENER_URL", "")
    SHORTENER_API = os.environ.get("SHORTENER_API", "")
    SHORTENER_ON = os.environ.get("SHORTENER_ON", "False").lower() == "true"
    [span_4](start_span)VERIFY_EXPIRE = 86400 # ২৪ ঘণ্টা (সেকেন্ডে)[span_4](end_span)
