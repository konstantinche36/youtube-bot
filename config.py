import os
from dotenv import load_dotenv

# Загружаем .env файл только если он существует
if os.path.exists('.env'):
    load_dotenv()
    print("DEBUG: .env file loaded")
else:
    print("DEBUG: .env file not found, using environment variables")

class Config:
    # Telegram Bot - ВРЕМЕННО ЗАХАРДКОЖЕНО ДЛЯ ТЕСТИРОВАНИЯ
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "7902497697:AAHqEzqa-diC8_8LFse8CVf0PoGoD8Bf8wE"
    
    # Отладочная информация
    print(f"DEBUG: TELEGRAM_BOT_TOKEN = {TELEGRAM_BOT_TOKEN}")
    print(f"DEBUG: TELEGRAM_BOT_TOKEN type = {type(TELEGRAM_BOT_TOKEN)}")
    print(f"DEBUG: TELEGRAM_BOT_TOKEN length = {len(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else 0}")
    
    # Проверяем все переменные окружения
    env_vars = {
        'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
        'DATABASE_URL': os.getenv("DATABASE_URL") or "sqlite:///./youtube_bot.db",
        'STORAGE_TYPE': os.getenv("STORAGE_TYPE") or "local",
        'LOG_LEVEL': os.getenv("LOG_LEVEL") or "INFO",
        'DEBUG': os.getenv("DEBUG") or "True"
    }
    print(f"DEBUG: Environment variables: {env_vars}")
    
    TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
    
    # Database
    DATABASE_URL = env_vars['DATABASE_URL']
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # File Storage
    STORAGE_TYPE = env_vars['STORAGE_TYPE']
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
    DEBUG = env_vars['DEBUG'].lower() == "true"
    LOG_LEVEL = env_vars['LOG_LEVEL']
    
    # Security
    ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",") if os.getenv("ALLOWED_USERS") else []
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", "10"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            print("ERROR: TELEGRAM_BOT_TOKEN is not set!")
            print("ERROR: Please set TELEGRAM_BOT_TOKEN environment variable")
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        if cls.STORAGE_TYPE == "s3" and not all([
            cls.AWS_ACCESS_KEY_ID, 
            cls.AWS_SECRET_ACCESS_KEY, 
            cls.AWS_S3_BUCKET
        ]):
            raise ValueError("AWS credentials are required for S3 storage") 