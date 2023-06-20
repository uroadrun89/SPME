import logging
import os
import json
from dotenv import dotenv_values
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.load_config()

    def load_config(self):
        try:
            token = dotenv_values(".env")["TELEGRAM_TOKEN"]
        except Exception as e:
            logger.error(f"Failed to load token from .env file: {e}")
            token = os.environ.get('TELEGRAM_TOKEN')
            if token is None:
                logger.error("Telegram token not found. Make sure to set TELEGRAM_TOKEN environment variable.")
                raise ValueError("Telegram token not found.")
        self.token = token
        self.auth_enabled = False  # Change to True if authentication is required
        self.auth_password = "your_password"  # Set the desired authentication password
        self.auth_users = []  # List of authorized user chat IDs

config = Config()

def authenticate(func):
    def wrapper(update, context):
        chat_id = update.effective_chat.id
        if config.auth_enabled:
            if chat_id not in config.auth_users:
                context.bot.send_message(chat_id=chat_id, text="⚠️ This bot is personal and you are not signed in. Please enter the password to sign in. If you don't know it, contact the bot owner.")
                return
        return func(update, context)
    return wrapper

def start(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text="Welcome to the Song Downloader Bot!")

def get_single_song(update, context):
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    username = update.effective_chat.username
    logger.info(f'Starting song download. Chat ID: {chat_id}, Message ID: {message_id}, Username: {username}')

    url = update.effective_message.text.strip()

    download_dir = f".temp{message_id}{chat_id}"
    os.makedirs(download_dir, exist_ok=True)
    os.chdir(download_dir)

    logger.info('Downloading song...')
    context.bot.send_message(chat_id=chat_id, text="Fetching...")

    if url.startswith(("http://", "https://")):
        os.system(f'spotdl download "{url}" --threads 12 --format mp3 --bitrate 320k --lyrics genius')

        logger.info('Sending song to user...')
        sent = 0
        files = [file for file in os.listdir(".") if file.endswith(".mp3")]
        if files:
            for file in files:
                context.bot.send_audio(chat_id=chat_id, audio=open(file, 'rb'), timeout=18000)
                sent += 1
            logger.info(f'Sent {sent} audio file(s) to user.')
        else:
            context.bot.send_message(chat_id=chat_id, text="Unable to find the requested song.")
            logger.warning('No audio file found after download.')
    else:
        context.bot.send_message(chat_id=chat_id, text="Invalid URL. Please provide a valid song URL.")
        logger.warning('Invalid URL provided.')

    os.chdir('..')
    os.system(f'rm -rf {download_dir}')

def main():
    updater = Updater(token=config.token, use_context=True)
    dispatcher = updater.dispatcher

    # Handlers
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    song_handler = MessageHandler(Filters.text & (~Filters.command), get_single_song)
    dispatcher.add_handler(song_handler)

    # Start the bot
    updater.start_polling()
    logger.info('Bot started.')
    updater.idle()

if __name__ == "__main__":
    main()
