from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from telegram import Bot
import json
import logging
import os
from dotenv import dotenv_values
import subprocess

# Load environment variables from .env file
config = dotenv_values(".env")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Create an instance of the Updater and pass your bot token
updater = Updater(token=config['BOT_TOKEN'], use_context=True)
dispatcher = updater.dispatcher

# Command handler for the /start command
def start(update, context):
    if 'password' not in context.chat_data or not context.args:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Please provide the password to start using the bot.')
        return

    password = context.args[0]
    if password == config['BOT_PASSWORD']:
        context.chat_data['password'] = password
        context.bot.send_message(chat_id=update.effective_chat.id, text='Authentication successful! You can now use the bot.')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Authentication failed! Incorrect password.')

# Command handler for the /download command
def download(update, context):
    if 'password' not in context.chat_data:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Please authenticate using the /start command.')
        return

    # Get the Spotify link from the message
    spotify_link = context.args[0]
    
    # Create a temporary folder to store the downloaded music files
    temp_folder = 'temp_folder'
    os.makedirs(temp_folder, exist_ok=True)

    # Download the music using spotdl
    os.system(f'spotdl --output {temp_folder} --output-format mp3 --song {spotify_link}')
    
    # Convert the downloaded music files to 320kbps using ffmpeg
    for file_name in os.listdir(temp_folder):
        if file_name.endswith('.mp3'):
            input_path = os.path.join(temp_folder, file_name)
            output_path = os.path.join(temp_folder, f'{file_name[:-4]}_320kbps.mp3')
            subprocess.run(['ffmpeg', '-i', input_path, '-b:a', '320k', output_path])

            # Send the music file to Telegram
            with open(output_path, 'rb') as audio_file:
                context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio_file)

    # Remove the temporary folder
    os.system(f'rm -rf {temp_folder}')

# Register the handlers
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('download', download))

# Start the bot
updater.start_polling()
