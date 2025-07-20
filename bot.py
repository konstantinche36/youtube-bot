import logging
import re
import os
from typing import Optional, Dict
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.sql import func
import asyncio
import os

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
try:
    Config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    print(f"ERROR: {e}")
    print("Please check your environment variables")
    exit(1)

# Initialize bot and dispatcher
bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=storage)
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
    try:
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
                session.commit()
            else:
                db_user.last_activity = func.now()
                session.commit()
    except Exception as e:
        logger.error(f"Database error: {e}")
        # Continue without database if there's an error
    
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
    
    try:
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
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await message.answer("❌ Ошибка при получении статистики")

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Handle /status command"""
    user = message.from_user
    if not user:
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    
    try:
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
    except Exception as e:
        logger.error(f"Status error: {e}")
        await message.answer("❌ Ошибка при получении статуса")

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

# Callback query handlers
@router.callback_query(lambda c: c.data.startswith('format_'))
async def handle_format_selection(callback: types.CallbackQuery, state: FSMContext):
    """Handle format selection"""
    format_type = callback.data.replace('format_', '')
    logger.info(f"Format selected: {format_type}")
    
    await state.update_data(format_type=format_type)
    
    await callback.message.answer(
        f"🎯 Выбран формат: {format_type.upper()}\n\n"
        "Теперь выберите качество:",
        reply_markup=get_quality_keyboard()
    )
    
    await state.set_state(DownloadStates.waiting_for_quality)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith('quality_'))
async def handle_quality_selection(callback: types.CallbackQuery, state: FSMContext):
    """Handle quality selection"""
    quality = callback.data.replace('quality_', '')
    logger.info(f"Quality selected: {quality}")
    
    data = await state.get_data()
    url = data.get('url', 'Unknown URL')
    format_type = data.get('format_type', 'Unknown')
    video_info = data.get('video_info', {})
    
    await callback.message.answer(
        f"🎬 Начинаю загрузку!\n\n"
        f"📹 Видео: {video_info.get('title', 'Unknown')}\n"
        f"🎯 Формат: {format_type.upper()}\n"
        f"⭐ Качество: {quality}\n\n"
        f"⏳ Загрузка началась..."
    )
    
    # Real download logic
    try:
        logger.info(f"Starting real download: {url}, format: {format_type}, quality: {quality}")
        
        # Download video
        success, file_path, download_info = await downloader.download_video_async(
            url, format_type, quality
        )
        
        if success and file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            
            # Check file size limit (50MB Telegram limit)
            if file_size > Config.MAX_FILE_SIZE:
                await callback.message.answer(
                    f"❌ Файл слишком большой: {format_file_size(file_size)}\n"
                    f"Максимальный размер: {format_file_size(Config.MAX_FILE_SIZE)}"
                )
                # Clean up large file
                downloader.cleanup_file(file_path)
                await state.clear()
                await callback.answer()
                return
            
            # Save to database
            user = callback.from_user
            if user:
                try:
                    with db.get_session() as session:
                        db_user = session.query(User).filter(User.telegram_id == user.id).first()
                        if db_user:
                            download_request = DownloadRequest(
                                user_id=db_user.id,
                                youtube_url=url,
                                video_title=video_info.get('title', 'Unknown'),
                                video_duration=video_info.get('duration', 0),
                                format_type=format_type,
                                quality=quality,
                                status="completed",
                                file_path=file_path,
                                file_size=file_size
                            )
                            session.add(download_request)
                            session.commit()
                except Exception as e:
                    logger.error(f"Database error: {e}")
            
            # Send file to user
            try:
                with open(file_path, 'rb') as file:
                    if format_type == "mp3":
                        await callback.message.answer_audio(
                            audio=file,
                            title=video_info.get('title', 'Unknown'),
                            performer=video_info.get('uploader', 'Unknown'),
                            duration=int(video_info.get('duration', 0))
                        )
                    else:
                        await callback.message.answer_video(
                            video=file,
                            caption=f"📹 {video_info.get('title', 'Unknown')}\n"
                                   f"🎯 Формат: {format_type.upper()}\n"
                                   f"⭐ Качество: {quality}\n"
                                   f"📏 Размер: {format_file_size(file_size)}"
                        )
                
                await callback.message.answer("✅ Загрузка завершена!")
                
                # Clean up file after sending
                downloader.cleanup_file(file_path)
                
            except Exception as e:
                logger.error(f"Error sending file: {e}")
                await callback.message.answer(f"❌ Ошибка отправки файла: {e}")
                downloader.cleanup_file(file_path)
        else:
            await callback.message.answer("❌ Ошибка загрузки видео. Попробуйте другой формат.")
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        await callback.message.answer(f"❌ Ошибка загрузки: {e}")
    
    await state.clear()
    await callback.answer()

@router.callback_query(lambda c: c.data == 'cancel')
async def handle_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Handle cancel"""
    await callback.message.answer("❌ Операция отменена")
    await state.clear()
    await callback.answer()

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