import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./youtube_bot.db")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # File Storage
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # local, s3, gcs
    LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "./downloads")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    
    # YouTube Download
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB Telegram limit
    SUPPORTED_FORMATS = ["mp4", "mp3", "webm"]
    DEFAULT_QUALITY = "best"
    
    # App Settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",") if os.getenv("ALLOWED_USERS") else []
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", "10"))  # requests per minute
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        if cls.STORAGE_TYPE == "s3" and not all([
            cls.AWS_ACCESS_KEY_ID, 
            cls.AWS_SECRET_ACCESS_KEY, 
            cls.AWS_S3_BUCKET
        ]):
            raise ValueError("AWS credentials are required for S3 storage") 