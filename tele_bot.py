from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import aiohttp
import os
from dotenv import load_dotenv
from telegram.constants import ParseMode
from pipeline.utils import convert_bold_to_html
from aiohttp import web

load_dotenv()
TELEGRAM_API = os.getenv("TELEGRAM_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Set this to your Render app's URL, e.g., https://your-app.onrender.com

def check_internet():
    try:
        response = requests.get("https://www.google.com", timeout=5)
        if response.status_code == 200:
            print("Internet connection is available.")
            return True
        else:
            print(f"Internet check failed with status code: {response.status_code}")
            return False
    except requests.ConnectionError as e:
        print(f"No internet connection: {e}")
        return False
        
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        convert_bold_to_html(f"Hello **{update.effective_user.first_name}**"),
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    response = await query_backend(user_message)
    await update.message.reply_text(convert_bold_to_html(response), parse_mode=ParseMode.HTML)

async def query_backend(user_message):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://carboncredits-tccv-edu-chatbot.hf.space/query",
            json={"user_message": user_message}
        ) as resp:
            response_data = await resp.json()
            return response_data["response"]

async def set_webhook():
    url = f"{WEBHOOK_URL}/webhook/{TELEGRAM_API}"
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            f"https://api.telegram.org/bot{TELEGRAM_API}/setWebhook",
            json={"url": url}
        )
        data = await response.json()
        if data.get("ok"):
            print(f"Webhook set successfully: {url} with {data}")
        else:
            print(f"Failed to set webhook: {data}")

async def webhook_handler(request):
    update_data = await request.json()
    application = request.app["application"]  # Retrieve the Application instance
    update = Update.de_json(update_data, application.bot)
    await application.update_queue.put(update)
    return web.Response(text="OK")

def main() -> None:
    # Create the application
    app = ApplicationBuilder().token(TELEGRAM_API).build()
    check_internet()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set the webhook asynchronously
    import asyncio
    asyncio.run(set_webhook())

    # Aiohttp app setup for Render
    aiohttp_app = web.Application()
    aiohttp_app["application"] = app  # Store the Application instance in aiohttp app
    aiohttp_app.router.add_post(f"/webhook/{TELEGRAM_API}", webhook_handler)

    # Run aiohttp server
    web.run_app(aiohttp_app, port=int(os.getenv("PORT", 8080)))

if __name__ == "__main__":
    main()
