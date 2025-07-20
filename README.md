# 🎬 YouTube Download Telegram Bot

Telegram бот для скачивания YouTube видео с поддержкой различных форматов и качеств.

## ✨ Возможности

- 📥 Скачивание YouTube видео в форматах MP4, MP3, WebM
- 🎯 Выбор качества видео
- 💾 Локальное и облачное хранилище (AWS S3)
- 📊 Статистика загрузок
- 🔒 Ограничение доступа по пользователям
- ⚡ Асинхронная обработка
- 📝 Логирование операций

## 🛠️ Технологии

- **Python 3.8+**
- **aiogram** - Telegram Bot API
- **yt-dlp** - YouTube скачивание
- **SQLAlchemy** - База данных
- **FastAPI** - Web API (опционально)
- **Redis** - Кэширование и очереди
- **AWS S3** - Облачное хранилище

## 📋 Требования

- Python 3.8 или выше
- Telegram Bot Token
- FFmpeg (для конвертации аудио)

## 🚀 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd youtube-telegram-bot
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Установка FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Скачайте с [официального сайта](https://ffmpeg.org/download.html)

### 4. Настройка конфигурации

Скопируйте пример конфигурации:
```bash
cp env_example.txt .env
```

Отредактируйте `.env` файл:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite:///./youtube_bot.db
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./downloads
```

### 5. Получение Telegram Bot Token

1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен в `.env`

## 🏃‍♂️ Запуск

### Простой запуск

```bash
python main.py
```

### Запуск с Docker

```bash
docker build -t youtube-bot .
docker run -d --name youtube-bot youtube-bot
```

### Запуск в production

```bash
# С использованием systemd
sudo systemctl start youtube-bot

# Или с supervisor
supervisord -c supervisor.conf
```

## 📖 Использование

### Основные команды

- `/start` - Начать работу с ботом
- `/help` - Показать справку
- `/stats` - Статистика загрузок
- `/status` - Статус активных загрузок

### Процесс скачивания

1. **Отправьте ссылку** на YouTube видео
2. **Выберите формат** (MP4, MP3, WebM)
3. **Выберите качество** (Лучшее, HD, Среднее)
4. **Дождитесь загрузки** и получите файл

### Примеры ссылок

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/dQw4w9WgXcQ
https://www.youtube.com/embed/dQw4w9WgXcQ
```

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | - |
| `DATABASE_URL` | URL базы данных | `sqlite:///./youtube_bot.db` |
| `STORAGE_TYPE` | Тип хранилища | `local` |
| `LOCAL_STORAGE_PATH` | Путь к локальному хранилищу | `./downloads` |
| `MAX_FILE_SIZE` | Максимальный размер файла | `52428800` (50MB) |
| `DEBUG` | Режим отладки | `False` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

### Типы хранилища

#### Локальное хранилище
```env
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./downloads
```

#### AWS S3
```env
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your_bucket
AWS_REGION=us-east-1
```

## 🗄️ База данных

### SQLite (по умолчанию)
```env
DATABASE_URL=sqlite:///./youtube_bot.db
```

### PostgreSQL
```env
DATABASE_URL=postgresql://user:password@localhost/youtube_bot
```

### Схема базы данных

- **users** - Пользователи бота
- **download_requests** - Запросы на скачивание
- **download_stats** - Статистика загрузок

## 🔧 Разработка

### Структура проекта

```
youtube-telegram-bot/
├── main.py              # Главный файл
├── bot.py               # Telegram бот
├── config.py            # Конфигурация
├── database.py          # База данных
├── models.py            # Модели данных
├── youtube_downloader.py # Скачивание YouTube
├── storage.py           # Файловое хранилище
├── utils.py             # Утилиты
├── requirements.txt     # Зависимости
├── env_example.txt      # Пример конфигурации
└── README.md           # Документация
```

### Добавление новых форматов

1. Обновите `Config.SUPPORTED_FORMATS`
2. Добавьте обработку в `youtube_downloader.py`
3. Обновите клавиатуру в `bot.py`

### Добавление новых хранилищ

1. Создайте новый класс в `storage.py`
2. Реализуйте методы `upload_file`, `delete_file`
3. Обновите `StorageManager`

## 📊 Мониторинг

### Логи

Логи сохраняются в файл `youtube_bot.log`:
```bash
tail -f youtube_bot.log
```

### Метрики

- Количество загрузок
- Размер файлов
- Время обработки
- Ошибки

## 🔒 Безопасность

### Ограничения

- Максимальный размер файла: 50MB
- Поддержка только YouTube ссылок
- Ограничение по пользователям
- Rate limiting

### Рекомендации

- Используйте HTTPS для webhook
- Ограничьте доступ по IP
- Регулярно обновляйте зависимости
- Мониторьте логи

## 🐛 Устранение неполадок

### Частые проблемы

1. **"Bot token not found"**
   - Проверьте переменную `TELEGRAM_BOT_TOKEN`

2. **"FFmpeg not found"**
   - Установите FFmpeg

3. **"Database error"**
   - Проверьте права доступа к файлу БД

4. **"Download failed"**
   - Проверьте интернет соединение
   - Убедитесь, что видео доступно

### Логи

```bash
# Просмотр ошибок
grep ERROR youtube_bot.log

# Просмотр загрузок
grep "Download progress" youtube_bot.log
```

## 📄 Лицензия

Этот проект предназначен для образовательных целей. Убедитесь, что вы соблюдаете авторские права при использовании.

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Создайте Pull Request

## 📞 Поддержка

- Создайте Issue в GitHub
- Обратитесь к администратору бота
- Проверьте документацию

---

**⚠️ Важно:** Используйте бота только для личных целей и соблюдайте авторские права! 