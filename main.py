import os
import logging
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# Логирование
logging.basicConfig(
    format='[%(asctime)s] %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

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

        user_id=message.from_user.id,
        username=username,
        message=message.text if message.text else "[non-text]"
    )

    # Не отправляет /start
    if message.text and message.text.strip() == "/start":
        await message.reply_text("Напиши свое сообщение или отправь фото.")
        return
        
    # Текст
    if message.text:
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Сообщение от: @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=message.text)
        await message.reply_text("Сообщение получено! Скоро оно будет опубликовано в канал.")
        return

    # Фото
    elif message.photo:
        caption = message.caption if message.caption else ""
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Фото от: @{username}")
        await context.bot.send_photo(chat_id=CREATOR_CHAT_ID, photo=message.photo[-1].file_id, caption=caption)
        await message.reply_text("Фото получено! Скоро оно будет опубликовано в канал.")
        return

    # Голосовое
    elif message.voice:
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Голосовое сообщение от: @{username}")
        await context.bot.send_voice(chat_id=CREATOR_CHAT_ID, voice=message.voice.file_id)
        await message.reply_text("Голосовое сообщение получено! Скоро оно будет опубликовано в канал.")
        return

    # Документ
    elif message.document:
        caption = message.caption if message.caption else ""
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Документ: @{username}")
        await context.bot.send_document(chat_id=CREATOR_CHAT_ID, document=message.document.file_id, caption=caption)
        await message.reply_text("Документ получен! Скоро он будет опубликован в канал.")
        return

        # Видео
    elif message.video:
        caption = message.caption if message.caption else ""
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Видео от: @{username}")
        await context.bot.send_video(chat_id=CREATOR_CHAT_ID, video=message.video.file_id, caption=caption)
        await message.reply_text("Видео получено! Скоро оно будет опубликовано в канал.")
        return

    # Видеосообщение (кружок)
    elif message.video_note:
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Видеосообщение от: @{username}")
        await context.bot.send_video_note(chat_id=CREATOR_CHAT_ID, video_note=message.video_note.file_id)
        await message.reply_text("Видеосообщение получено! Скоро оно будет опубликовано в канал.")
        return

    # Неизвестный тип
    else:
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"Неизвестный тип сообщения от: @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text="[неизвестный тип сообщения]")

# Команда /log — отправка базы данных
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
    app.add_handler(MessageHandler(filters.ALL, forward))
    logging.info("Бот запущен ✅ с Webhook")
    app.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url=WEBHOOK_URL
    )
