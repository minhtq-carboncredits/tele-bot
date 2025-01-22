from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, WebhookHandler, filters
import aiohttp
import os
from dotenv import load_dotenv
from telegram.constants import ParseMode
from pipeline.utils import convert_bold_to_html
from aiohttp import web

load_dotenv()
TELEGRAM_API = os.getenv("TELEGRAM_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Set this to your Render app's public URL

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        convert_bold_to_html(f"Hello **{update.effective_user.first_name}**"), parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    response = await query_backend(user_message)
    await update.message.reply_text(
        convert_bold_to_html(response), parse_mode=ParseMode.HTML
    )

async def query_backend(user_message):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://carboncredits-tccv-edu-chatbot.hf.space/query", json={"user_message": user_message}
        ) as resp:
            response_data = await resp.json()
            return response_data["response"]

async def set_webhook(app):
    await app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")

async def webhook_handler(request: web.Request):
    bot = request.app["bot"]
    update = await bot.update_queue.put(await request.json())
    return web.Response()

def main() -> None:
    # Initialize the bot and application
    app = ApplicationBuilder().token(TELEGRAM_API).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add webhook settings
    app.on_startup.append(set_webhook)
    app.web_app.router.add_post("/webhook", webhook_handler)
    app.web_app["bot"] = app.bot

    # Run the application
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        webhook_url=f"{WEBHOOK_URL}/webhook",
    )

if __name__ == "__main__":
    main()
