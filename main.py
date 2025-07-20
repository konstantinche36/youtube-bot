#!/usr/bin/env python3
"""
YouTube Download Telegram Bot
Main entry point
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from database import init_database
from bot import main as bot_main

def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, Config.LOG_LEVEL.upper())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('youtube_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def validate_config():
    """Validate configuration"""
    try:
        Config.validate()
        logging.info("Configuration validated successfully")
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    directories = [
        Config.LOCAL_STORAGE_PATH,
        "logs",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {directory}")

async def main():
    """Main application entry point"""
    print("🎬 YouTube Download Telegram Bot")
    print("=" * 40)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Validate configuration
        validate_config()
        
        # Create directories
        create_directories()
        
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        
        # Start bot
        logger.info("Starting Telegram bot...")
        await bot_main()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 