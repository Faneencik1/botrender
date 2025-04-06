import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 🔇 Отключаем лишние логи от сторонних библиотек
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# ✅ Настройка логирования в файл и консоль
logging.basicConfig(
    format='[%(asctime)s] %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CREATOR_CHAT_ID = int(os.getenv("CREATOR_CHAT_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Пример: https://your-render-url.onrender.com

async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    username = message.from_user.username or message.from_user.id

    if message.text and message.text.strip() == "/start":
        return

    if message.text:
        logging.info(f"Сообщение от @{username}: {message.text}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"@{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=message.text)

    elif message.photo:
        caption = message.caption if message.caption else ""
        logging.info(f"Фото от @{username} (с подписью: {caption})")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"@{username}")
        await context.bot.send_photo(chat_id=CREATOR_CHAT_ID, photo=message.photo[-1].file_id, caption=caption)

    elif message.voice:
        logging.info(f"Голосовое сообщение от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"@{username}")
        await context.bot.send_voice(chat_id=CREATOR_CHAT_ID, voice=message.voice.file_id)

    elif message.document:
        caption = message.caption if message.caption else ""
        logging.info(f"Документ от @{username}: {message.document.file_name} (с подписью: {caption})")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"@{username}")
        await context.bot.send_document(chat_id=CREATOR_CHAT_ID, document=message.document.file_id, caption=caption)

    else:
        logging.info(f"Неизвестный тип сообщения от @{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text=f"@{username}")
        await context.bot.send_message(chat_id=CREATOR_CHAT_ID, text="[неизвестный тип сообщения]")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, forward))
    logging.info("Бот запущен ✅ с Webhook")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=WEBHOOK_URL
    )
