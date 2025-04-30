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

# Кэш для медиагрупп
media_group_cache = defaultdict(list)

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
        caption = message.caption if message.caption else None
        
        if message.photo:
            # Для первого элемента в группе добавляем подпись
            if message.media_group_id not in media_group_cache:
                media = InputMediaPhoto(
                    media=message.photo[-1].file_id,
                    caption=caption
                )
                media_group_cache[message.media_group_id] = {
                    'media_list': [media],
                    'username': username,
                    'message': message
                }
            else:
                media = InputMediaPhoto(media=message.photo[-1].file_id)
                media_group_cache[message.media_group_id]['media_list'].append(media)
        
        elif message.video:
            # Для первого элемента в группе добавляем подпись
            if message.media_group_id not in media_group_cache:
                media = InputMediaVideo(
                    media=message.video.file_id,
                    caption=caption
                )
                media_group_cache[message.media_group_id] = {
                    'media_list': [media],
                    'username': username,
                    'message': message
                }
            else:
                media = InputMediaVideo(media=message.video.file_id)
                media_group_cache[message.media_group_id]['media_list'].append(media)
        
        else:
            return

        # Ждем 1 секунду перед обработкой группы
        await asyncio.sleep(1)
        
        # Проверяем, что группа еще не обработана
        if message.media_group_id in media_group_cache:
            group = media_group_cache.pop(message.media_group_id)
            await context.bot.send_message(
                chat_id=CREATOR_CHAT_ID,
                text=f"Альбом из {len(group['media_list'])} медиа от @{username}"
            )
            await context.bot.send_media_group(
                chat_id=CREATOR_CHAT_ID,
                media=group['media_list']
            )
            await group['message'].reply_text(
                f"Альбом из {len(group['media_list'])} медиа получен! Скоро будет опубликован."
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

    if message.text:
        logger.info(f"Текст от @{username}: {message.text}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Сообщение от: @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=message.text)
        await message.reply_text("Сообщение получено! Скоро будет опубликовано.")
        return

    if message.voice:
        logger.info(f"Голосовое от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Голосовое от: @{username}")
        await context.bot.send_voice(chat_id=CREATOR_CHAT_ID, voice=message.voice.file_id)
        await message.reply_text("Голосовое сообщение получено!")
        return

    if message.document:
        caption = message.caption if message.caption else ""
        logger.info(f"Документ от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Документ от: @{username}")
        await context.bot.send_document(
            chat_id=CREATOR_CHAT_ID,
            document=message.document.file_id,
            caption=caption
        )
        await message.reply_text("Документ получен!")
        return

    if message.video_note:
        logger.info(f"Видеокружок от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Видеосообщение от: @{username}")
        await context.bot.send_video_note(chat_id=CREATOR_CHAT_ID, video_note=message.video_note.file_id)
        await message.reply_text("Видеосообщение получено!")
        return

    logger.info(f"Неизвестный тип от @{username}")
    await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Неизвестный тип от: @{username}")
    await message.reply_text("Этот тип сообщений пока не поддерживается.")

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
