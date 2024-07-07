import os
import requests
import logging
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the token from environment variable
TOKEN = os.getenv("BOT_TOKEN")

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
            await query.message.reply_photo(photo=news['image_url'], caption=news['text'])
        else:
            await query.message.reply_text("Sorry, couldn't fetch news at the moment. Please try again later.")

def fetch_news():
    url = "https://inshorts.com/en/read"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        soup = BeautifulSoup(response.content, 'html.parser')
        
        news_cards = soup.find_all('div', class_='news-card')
        if news_cards:
            card = news_cards[0]  # Get the first news card
            image_url = card.find('div', class_='news-card-image')['style'].split("'")[1]
            text = card.find('div', class_='news-card-content').find('div', class_='news-card-body').text.strip()
            logger.info("News fetched successfully")
            return {'image_url': image_url, 'text': text}
        else:
            logger.error("No news cards found on the page")
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return None

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    logger.info("Starting bot")
    application.run_polling()

if __name__ == "__main__":
    main()
