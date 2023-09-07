import requests
from alembic.command import upgrade
from alembic.config import Config
from sqlalchemy_utils import create_database, database_exists
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.logger import get_logger
from app.service import (
    get_chat_id_by_message,
    get_chat_message_from_id,
    get_response_by_id,
    save_model_response,
    save_support_message,
)
from app.settings import Settings

logger = get_logger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message is None:
        return
    logger.info(f"Start command {update.effective_message.chat_id}")
    await update.message.reply_text(
        "Привет, я бот поддержки от команды LLamaGen. Напиши сообщение, чтобы оно передалось в поддержку."
    )


async def support_response_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_message = await get_chat_id_by_message(
        update.effective_message.reply_to_message.text, update.effective_message.reply_to_message.date
    )
    if chat_message is None:
        logger.info("Chat message not found")
        return
    chat_id, message_id = chat_message
    await context.bot.send_message(chat_id=chat_id, text=update.effective_message.text, reply_to_message_id=message_id)
    logger.info(f"Send message {update.effective_message.text} to {chat_id}")


async def generate_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message_db_id: int) -> None:
    message_text = update.effective_message.text
    logger.info(f"Generate message {message_text}")
    response = requests.get(Settings().API_URL + "/message", params={"message": message_text})
    if response.status_code != 200:
        logger.error(f"Error generate message: {response.text}")
        return
    response_message = response.json()["message"]
    response_id = await save_model_response(response_message)
    keyboard = [
        [
            InlineKeyboardButton("Ответить?", callback_data=f"{message_db_id}|{response_id}"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=Settings().SUPPORT_CHAT_ID, text=response_message, reply_markup=reply_markup)
    logger.info(f"Send message {response_message}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id == Settings().SUPPORT_CHAT_ID:
        if update.effective_message.reply_to_message is None:
            return
        await support_response_text(update, context)
        return
    logger.info(f"Message from {chat_id}: {update.effective_message.text}")
    await update.message.reply_text("Сообщение передано в поддержку.")
    date = update.effective_message.date.replace(tzinfo=None)
    message_db_id = await save_support_message(
        update.effective_message.text, update.effective_message.id, chat_id, date
    )
    await update.message.forward(chat_id=Settings().SUPPORT_CHAT_ID)
    await generate_message(update, context, message_db_id)


def upgrade_database() -> None:
    settings = Settings()
    if not database_exists(settings.database_uri_sync):
        create_database(settings.database_uri_sync)
    config = Config("alembic.ini")
    config.attributes["configure_logger"] = False
    upgrade(config, "head")
    logger.info("Migrations done")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Button handler {update.callback_query.data}")
    query = update.callback_query
    await query.answer()
    request_id = int(query.data.split("|")[0])
    response_id = int(query.data.split("|")[1])
    chat_message = await get_chat_message_from_id(request_id)
    if chat_message is None:
        logger.error(f"Chat message not found for {request_id}")
        return
    chat_id, message_id = chat_message
    message = await get_response_by_id(response_id)
    await context.bot.send_message(chat_id=chat_id, text=message, reply_to_message_id=message_id)
    await query.message.edit_text(query.message.text)
    logger.info(f"Message send for {chat_id}")


def main() -> None:
    logger.info("Run migrations")
    upgrade_database()
    logger.info("Starting bot")
    app = ApplicationBuilder().token(Settings().BOT_KEY).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
