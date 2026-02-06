import os

class Config:
    API_ID = int(os.environ.get("API_ID", ""))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    MONGO_URI = os.environ.get("MONGO_URI", "")
    DB_NAME = os.environ.get("DB_NAME", "VideoBot")
    FSUB_CHANNEL = int(os.environ.get("FSUB_CHANNEL", "-100")) 
    
    # ৫টি চ্যানেলের আইডি
    CHANNELS = {
        "indian": int(os.environ.get("INDIAN_CH", "-100")),
        "english": int(os.environ.get("ENGLISH_CH", "-100")),
        "onlyfan": int(os.environ.get("ONLYFAN_CH", "-100")),
        "japanese": int(os.environ.get("JAPANESE_CH", "-100")),
        "viral": int(os.environ.get("VIRAL_CH", "-100"))
    }
    
    # শর্টনার সেটিংস
    SHORTENER_ON = os.environ.get("SHORTENER_ON", "False").lower() == "true"
