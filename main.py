import json
import logging
import os
import subprocess

from dotenv import dotenv_values
from telegram import Bot
from telegram.ext import Updater, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

def authenticate(update, context):
    chat_id = update.effective_message.chat_id
    config = load_config()
    if update.effective_message.text == config["AUTH"]["PASSWORD"]:
        logging.log(logging.INFO, f'new sign in for user {update.message.chat.username}, {chat_id}')
        config["AUTH"]["USERS"].append(chat_id)
        save_config(config)
        context.bot.send_message(chat_id=chat_id, text="You signed in successfully. Enjoy🍻")
        raise Exception("Signed In")
    elif chat_id not in config["AUTH"]["USERS"]:
        logging.log(logging.INFO, f'not authenticated try')
        context.bot.send_message(chat_id=chat_id, text="⚠️ This bot is personal and you are not signed in. Please enter the "
                                                       "password to sign in. If you don't know it, contact the bot owner.")
        raise Exception("Not Signed In")

def get_single_song(update, context, url):
    chat_id = update.effective_message.chat_id
    message_id = update.effective_message.message_id
    username = update.message.chat.username
    logging.log(logging.INFO, f'start to query message {message_id} in chat:{chat_id} from {username}')

    url = "'" + url + "'"

    logging.log(logging.INFO, f'start downloading')
    context.bot.send_message(chat_id=chat_id, text="Fetching...")

    downloader = config.get("DOWNLOADER")
    if downloader == "spotdl":
        subprocess.run(["spotdl", "download", url, "--threads", "12", "--format", "mp3", "--bitrate", "320k", "--lyrics", "genius"])
    elif downloader == "spotifydl":
        subprocess.run(["spotifydl", url])
    else:
        logging.log(logging.ERROR, 'you should select one of the downloaders')

    logging.log(logging.INFO, 'sending to client')
    try:
        sent = 0
        context.bot.send_message(chat_id=chat_id, text="Sending to you...")
        files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(".") for f in filenames if os.path.splitext(f)[1] == '.mp3']
        for file in files:
            with open(file, "rb") as audio_file:
                context.bot.send_audio(chat_id=chat_id, audio=audio_file, timeout=18000)
            sent += 1
    except:
        pass

    if sent == 0:
        context.bot.send_message(chat_id=chat_id, text="It seems there was a problem in finding/sending the song.")
        raise Exception("dl Failed")
    else:
        logging.log(logging.INFO, 'sent')

def get_single_song_handler(update, context):
    if config["AUTH"]["ENABLE"]:
        authenticate(update, context)
    
    urls = update.effective_message.text.split("\n")
    for url in urls:
        get_single_song(update, context, url)

def main():
    try:
        token = dotenv_values(".env")["TELEGRAM_TOKEN"]
    except:
        token = os.environ.get('TELEGRAM_TOKEN')
    if not token:
        raise ValueError("Telegram token not provided.")

    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    global config
    config = load_config()

    handler = MessageHandler(Filters.text, get_single_song_handler)
    dispatcher.add_handler(handler=handler)

    POLLING_INTERVAL = 0.5
    updater.start_polling(poll_interval=POLLING_INTERVAL)
    updater.idle()

if __name__ == "__main__":
    main()
