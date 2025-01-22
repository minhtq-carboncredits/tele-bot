from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import requests
from dotenv import load_dotenv
from pipeline.utils import convert_bold_to_html  # Replace with your utility path

# Load environment variables
load_dotenv()
TELEGRAM_API = os.getenv("TELEGRAM_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: https://yourapp.onrender.com/

# Register webhook with Telegram
def set_webhook():
    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_API}/setWebhook",
        json={"url": f"{WEBHOOK_URL}/{TELEGRAM_API}"}
    )
    print(response.json())

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        convert_bold_to_html(f"Hello **{update.effective_user.first_name}**"), 
        parse_mode="HTML"
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    response = await query_backend(user_message)
    await update.message.reply_text(
        convert_bold_to_html(response), 
        parse_mode="HTML"
    )

# Query backend for message processing
async def query_backend(user_message: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://carboncredits-tccv-edu-chatbot.hf.space/query", 
            json={"user_message": user_message}
        ) as resp:
            response_data = await resp.json()
            return response_data.get("response", "Error: No response from backend")

# Webhook handler
async def webhook_handler(request):
    # Extract update from the incoming POST request
    update = Update.de_json(await request.json(), app.bot)  # Use `app.bot` instead of undefined `context.bot`
    await app.process_update(update)  # Pass the update to the application for processing
    return web.Response(text="OK")  # Return OK to Telegram

# Main entry point
def main() -> None:
    global app
    set_webhook()

    # Initialize Telegram bot application
    app = ApplicationBuilder().token(TELEGRAM_API).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set up aiohttp web server
    web_app = web.Application()
    web_app.router.add_post(f"/{TELEGRAM_API}", webhook_handler)

    # Run the web server
    web.run_app(web_app, host="0.0.0.0", port=8443)

if __name__ == "__main__":
    main()
