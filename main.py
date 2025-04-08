import os
import logging
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# Настраиваем свой логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("log.txt", encoding="utf-8")
file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
logger.addHandler(file_handler)

# Отключаем лишние логи от библиотек
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CREATOR_CHAT_ID = int(os.getenv("CREATOR_CHAT_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ALLOWED_USERS = {CREATOR_CHAT_ID, 6811659941}

# Основной обработчик сообщений
async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    username = message.from_user.username or message.from_user.id

    if message.text and message.text.strip() == "/start":
        await message.reply_text("Напиши свое сообщение или отправь фото.")
        return

    if message.text:
        logger.info(f"Текст от @{username}: {message.text}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Сообщение от: @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=message.text)
        await message.reply_text("Сообщение получено! Скоро оно будет опубликовано в канал.")
        return

    elif message.photo:
        caption = message.caption if message.caption else ""
        logger.info(f"Фото от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Фото от: @{username}")
        await context.bot.send_photo(chat_id=CREATOR_CHAT_ID, photo=message.photo[-1].file_id, caption=caption)
        await message.reply_text("Фото получено! Скоро оно будет опубликовано в канал.")
        return

    elif message.voice:
        logger.info(f"Голосовое от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Голосовое сообщение от: @{username}")
        await context.bot.send_voice(chat_id=CREATOR_CHAT_ID, voice=message.voice.file_id)
        await message.reply_text("Голосовое сообщение получено! Скоро оно будет опубликовано в канал.")
        return

    elif message.document:
        caption = message.caption if message.caption else ""
        logger.info(f"Документ от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Документ: @{username}")
        await context.bot.send_document(chat_id=CREATOR_CHAT_ID, document=message.document.file_id, caption=caption)
        await message.reply_text("Документ получен! Скоро он будет опубликован в канал.")
        return

    elif message.video:
        caption = message.caption if message.caption else ""
        logger.info(f"Видео от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Видео от: @{username}")
        await context.bot.send_video(chat_id=CREATOR_CHAT_ID, video=message.video.file_id, caption=caption)
        await message.reply_text("Видео получено! Скоро оно будет опубликовано в канал.")
        return

    elif message.video_note:
        logger.info(f"Кружок от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Видеосообщение от: @{username}")
        await context.bot.send_video_note(chat_id=CREATOR_CHAT_ID, video_note=message.video_note.file_id)
        await message.reply_text("Видеосообщение получено! Скоро оно будет опубликовано в канал.")
        return

    else:
        logger.info(f"Неизвестный тип от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Неизвестный тип сообщения от: @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text="[неизвестный тип сообщения]")

# Команда /log — отправка логов
async def send_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("Недостаточно прав для доступа к логам.")
        return

    if os.path.exists("log.txt"):
        with open("log.txt", "rb") as log_file:
            await update.message.reply_document(document=InputFile(log_file), filename="log.txt")
    else:
        await update.message.reply_text("Файл логов не найден.")

# Запуск бота
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
