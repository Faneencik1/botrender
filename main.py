import os
import logging
import asyncio
from datetime import datetime
from collections import defaultdict
from telegram import Update, InputFile, InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_date = datetime.now().strftime("%Y-%m-%d")
log_filename = f"log_{log_date}.txt"

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(file_handler)

# Отключаем лишние логи
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CREATOR_CHAT_ID = int(os.getenv("CREATOR_CHAT_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ALLOWED_USERS = {CREATOR_CHAT_ID, 6811659941}

# Глобальные переменные для обработки медиагрупп
media_groups = {}
media_group_tasks = {}

async def process_media_group(media_group_id, context, username, message):
    # Ждем 3 секунды для сбора всех медиа в группе
    await asyncio.sleep(3)
    
    if media_group_id in media_groups:
        media_list = media_groups.pop(media_group_id)
        if media_group_id in media_group_tasks:
            media_group_tasks.pop(media_group_id)
        
        if len(media_list) > 0:
            # Добавляем подпись только к первому медиа
            if media_list[0].caption is None and message.caption:
                media_list[0].caption = message.caption
            
            await context.bot.send_message(
                chat_id=CREATOR_CHAT_ID,
                text=f"Альбом из {len(media_list)} медиа от @{username}"
            )
            await context.bot.send_media_group(
                chat_id=CREATOR_CHAT_ID,
                media=media_list
            )
            await message.reply_text(
                f"Альбом из {len(media_list)} медиа получен! Скоро будет опубликован."
            )

async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    username = message.from_user.username or message.from_user.id

    if message.text and message.text.strip() == "/start":
        await message.reply_text("Напиши свое сообщение или отправь фото.")
        return

    # Обработка медиагрупп (альбомов)
    if hasattr(message, 'media_group_id') and message.media_group_id:
        media_group_id = message.media_group_id
        
        if message.photo:
            media = InputMediaPhoto(media=message.photo[-1].file_id)
        elif message.video:
            media = InputMediaVideo(media=message.video.file_id)
        else:
            return

        # Добавляем медиа в группу
        if media_group_id not in media_groups:
            media_groups[media_group_id] = []
            # Для первого элемента можно сразу установить подпись
            if message.caption:
                media.caption = message.caption
        
        media_groups[media_group_id].append(media)
        
        # Управляем таймером обработки группы
        if media_group_id in media_group_tasks:
            media_group_tasks[media_group_id].cancel()
        
        media_group_tasks[media_group_id] = asyncio.create_task(
            process_media_group(media_group_id, context, username, message)
        )
        return

    # Обработка одиночных медиа
    if message.photo:
        caption = message.caption if message.caption else ""
        logger.info(f"Фото от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Фото от: @{username}")
        await context.bot.send_photo(
            chat_id=CREATOR_CHAT_ID,
            photo=message.photo[-1].file_id,
            caption=caption
        )
        await message.reply_text("Фото получено! Скоро будет опубликовано.")
        return

    if message.video:
        caption = message.caption if message.caption else ""
        logger.info(f"Видео от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Видео от: @{username}")
        await context.bot.send_video(
            chat_id=CREATOR_CHAT_ID,
            video=message.video.file_id,
            caption=caption
        )
        await message.reply_text("Видео получено! Скоро будет опубликовано.")
        return

    # Остальные обработчики (текст, голосовые, документы) остаются без изменений
    # ...

async def send_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("Недостаточно прав для доступа к логам.")
        return

    log_date = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"log_{log_date}.txt"

    if os.path.exists(log_filename):
        with open(log_filename, "rb") as log_file:
            await update.message.reply_document(document=InputFile(log_file), filename=log_filename)
    else:
        await update.message.reply_text("Файл логов за сегодня не найден.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("log", send_log))
    app.add_handler(MessageHandler(filters.ALL, forward))
    logger.info("Бот запущен ✅ с Webhook")
    app.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url=WEBHOOK_URL
    )
