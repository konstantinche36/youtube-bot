import logging
import re
from typing import Optional, Dict
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.sql import func
import asyncio

from config import Config
from database import db
from models import User, DownloadRequest
from youtube_downloader import downloader
from storage import storage
from utils import validate_youtube_url, format_file_size, format_duration

# Configure logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Validate configuration
if not Config.TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is required")

# Initialize bot and dispatcher
bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)  # type: ignore
dp = Dispatcher()
router = Router()

# States for FSM
class DownloadStates(StatesGroup):
    waiting_for_url = State()
    waiting_for_format = State()
    waiting_for_quality = State()

# Inline keyboards
def get_format_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎥 MP4 Video", callback_data="format_mp4"),
            InlineKeyboardButton(text="🎵 MP3 Audio", callback_data="format_mp3")
        ],
        [
            InlineKeyboardButton(text="📱 WebM", callback_data="format_webm"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
        ]
    ])
    return keyboard

def get_quality_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏆 Лучшее", callback_data="quality_best"),
            InlineKeyboardButton(text="📺 HD", callback_data="quality_hd")
        ],
        [
            InlineKeyboardButton(text="📱 Среднее", callback_data="quality_medium"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
        ]
    ])
    return keyboard

# Command handlers
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    user = message.from_user
    if not user:
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    
    # Save user to database
    with db.get_session() as session:
        db_user = session.query(User).filter(User.telegram_id == user.id).first()
        if not db_user:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(db_user)
        else:
            db_user.last_activity = db.get_session_sync().query(func.now()).scalar()
    
    welcome_text = f"""
🎬 Привет, {user.first_name}!

Я бот для скачивания YouTube видео. Просто отправь мне ссылку на видео!

📋 Доступные команды:
/start - Начать работу
/help - Помощь
/stats - Статистика
/status - Статус загрузок

⚠️ Используй только для личных целей!
    """
    
    await message.answer(welcome_text)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    help_text = """
📖 Как использовать бота:

1️⃣ Отправь ссылку на YouTube видео
2️⃣ Выбери формат (MP4, MP3, WebM)
3️⃣ Выбери качество
4️⃣ Дождись загрузки

📋 Поддерживаемые форматы:
• 🎥 MP4 - видео файлы
• 🎵 MP3 - аудио файлы  
• 📱 WebM - веб видео

⚠️ Ограничения:
• Максимальный размер: 50MB
• Только для личного использования
• Не нарушайте авторские права

🆘 Если что-то не работает:
• Проверь правильность ссылки
• Попробуй другой формат
• Обратись к администратору
    """
    
    await message.answer(help_text)

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Handle /stats command"""
    user = message.from_user
    if not user:
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    
    with db.get_session() as session:
        db_user = session.query(User).filter(User.telegram_id == user.id).first()
        if not db_user:
            await message.answer("❌ Пользователь не найден")
            return
        
        # Get user statistics
        total_downloads = session.query(DownloadRequest).filter(
            DownloadRequest.user_id == db_user.id,
            DownloadRequest.status == "completed"
        ).count()
        
        recent_downloads = session.query(DownloadRequest).filter(
            DownloadRequest.user_id == db_user.id
        ).order_by(DownloadRequest.created_at.desc()).limit(5).all()
    
    stats_text = f"""
📊 Статистика пользователя {user.first_name}:

📥 Всего загрузок: {total_downloads}
📅 Дата регистрации: {db_user.created_at.strftime('%d.%m.%Y')}

🕐 Последние загрузки:
"""
    
    for download in recent_downloads:
        status = str(download.status)
        if status == "completed":
            status_emoji = "✅"
        elif status == "processing":
            status_emoji = "⏳"
        else:
            status_emoji = "❌"
        stats_text += f"{status_emoji} {download.video_title[:30]}... ({status})\n"
    
    await message.answer(stats_text)

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Handle /status command"""
    user = message.from_user
    if not user:
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    
    with db.get_session() as session:
        db_user = session.query(User).filter(User.telegram_id == user.id).first()
        if not db_user:
            await message.answer("❌ Пользователь не найден")
            return
        
        # Get active downloads
        active_downloads = session.query(DownloadRequest).filter(
            DownloadRequest.user_id == db_user.id,
            DownloadRequest.status.in_(["pending", "processing"])
        ).all()
    
    if not active_downloads:
        await message.answer("✅ Нет активных загрузок")
        return
    
    status_text = "⏳ Активные загрузки:\n\n"
    for download in active_downloads:
        status = str(download.status)
        if status == "processing":
            status_emoji = "⏳"
        else:
            status_emoji = "📋"
        status_text += f"{status_emoji} {download.video_title[:30]}... ({status})\n"
    
    await message.answer(status_text)

# Message handlers
@router.message()
async def handle_message(message: types.Message, state: FSMContext):
    """Handle all messages"""
    logger.info(f"Received message: {message.text}")
    
    if not message.text:
        await message.answer("❌ Отправьте текстовое сообщение")
        return
        
    text = message.text.strip()
    logger.info(f"Processing text: {text}")
    
    # Check if it's a YouTube URL
    if validate_youtube_url(text):
        logger.info("Valid YouTube URL detected")
        await handle_youtube_url(message, text, state)
    else:
        logger.info("Not a YouTube URL")
        await message.answer(
            "❌ Это не похоже на ссылку YouTube. "
            "Отправь мне ссылку на YouTube видео для скачивания."
        )

async def handle_youtube_url(message: types.Message, url: str, state: FSMContext):
    """Handle YouTube URL"""
    logger.info(f"Starting to handle YouTube URL: {url}")
    
    user = message.from_user
    if not user:
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    
    # Check rate limiting
    if not await check_rate_limit(user.id):
        await message.answer("⚠️ Слишком много запросов. Попробуй через минуту.")
        return
    
    # Get video info
    logger.info("Getting video info...")
    await message.answer("🔍 Получаю информацию о видео...")
    
    # Get video information
    try:
        video_info = downloader.get_video_info(url)
        if not video_info:
            # Временная заглушка для тестирования
            video_info = {
                'title': 'Тестовое видео',
                'duration': 120,
                'uploader': 'Test Channel'
            }
            logger.info("Using fallback video info")
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        video_info = {
            'title': 'Видео (ошибка получения)',
            'duration': 0,
            'uploader': 'Unknown'
        }
    
    if not video_info:
        await message.answer("❌ Не удалось получить информацию о видео. Проверьте ссылку.")
        return
    
    logger.info(f"Video info received: {video_info['title']}")
    
    # Save URL to state
    await state.update_data(url=url, video_info=video_info)
    
    # Show format selection
    await message.answer(
        f"📹 **{video_info['title']}**\n\n"
        f"⏱ Длительность: {format_duration(video_info['duration'])}\n"
        f" Автор: {video_info['uploader']}\n\n"
        "Выберите формат для скачивания:",
        reply_markup=get_format_keyboard()
    )
    
    # Set state
    await state.set_state(DownloadStates.waiting_for_format)

async def check_rate_limit(user_id: int) -> bool:
    """Check if user has exceeded rate limit"""
    # Simple rate limiting - can be enhanced with Redis
    return True  # For now, allow all requests

async def main():
    """Main function"""
    logger.info("Starting bot...")
    
    # Include router in dispatcher
    dp.include_router(router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 