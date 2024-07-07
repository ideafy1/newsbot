import os
import requests
import logging
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import random

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the token and URL from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get('PORT', 8080))
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("Send News", callback_data="send_news")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Press the button to get news:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "send_news":
        news = fetch_news()
        if news:
            message = f"*{news['title']}*\n\n{news['summary']}\n\n[Read more]({news['link']})"
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("Sorry, couldn't fetch news at the moment. Please try again later.")

def fetch_news():
    url = "https://en.wikinews.org/wiki/Main_Page"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        news_items = soup.find_all('div', class_='mw-headline')
        if news_items:
            news_item = random.choice(news_items)
            title = news_item.text.strip()
            
            summary = news_item.find_next('p').text.strip()
            
            full_article_link = news_item.find_next('a', string='Full article')
            if full_article_link:
                link = 'https://en.wikinews.org' + full_article_link['href']
            else:
                link = url
            
            logger.info("News fetched successfully")
            return {'title': title, 'summary': summary, 'link': link}
        else:
            logger.error("No news items found on the page")
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return None

async def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    logger.info("Starting bot")
    if RENDER_EXTERNAL_URL:
        await application.bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/webhook")
        await application.start()
        await application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{RENDER_EXTERNAL_URL}/webhook"
        )
    else:
        await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
