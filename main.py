import os
import json
import spotipy
import spotipy.util as util
import telebot
import requests
from dotenv import load_dotenv
from threading import Thread
import ffmpeg

load_dotenv()

# Load configuration from config.json
with open('config.json') as f:
    config = json.load(f)

# Load environment variables from .env
SPOTIFY_USERNAME = os.getenv('SPOTIFY_USERNAME')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID') or config['spotify_client_id']
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET') or config['spotify_client_secret']
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or config['telegram_bot_token']

# Authentication credentials from config.json
AUTHENTICATION_METHOD = config['authentication']['method']
AUTHENTICATION_USERNAME = config['authentication']['username']
AUTHENTICATION_PASSWORD = config['authentication']['password']

# Authenticate with Spotify
scope = 'user-library-read'
token = util.prompt_for_user_token(SPOTIFY_USERNAME, scope, client_id=SPOTIFY_CLIENT_ID,
                                   client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri='http://localhost/')

if token:
    sp = spotipy.Spotify(auth=token)
else:
    raise ValueError('Failed to authenticate with Spotify.')

# Initialize Telegram bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def download_file(url, filename):
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return filename


def convert_to_mp3(input_file, output_file):
    ffmpeg.input(input_file).output(output_file, audio_bitrate='320k', threads=12).run()


def delete_temp_folder(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
    os.rmdir(folder_path)


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Welcome to the Spotify Downloader Bot! Send me the name of an artist, playlist, album, "
                          "or track, and I'll send you the download link.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    query = message.text
    chat_id = message.chat.id

    # Create a temporary folder to store downloaded files
    temp_folder = 'temp'
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    try:
        search_result = sp.search(q=query, limit=1, type='track')
        track = search_result['tracks']['items'][0]
        track_name = track['name']
        track_artists = ', '.join([artist['name'] for artist in track['artists']])
        track_url = track['preview_url']

        if track_url:
            download_thread = Thread(target=download_file, args=(track_url, f'{temp_folder}/{track_name}.ogg'))
            download_thread.start()

            bot.send_message(chat_id, f'Downloading: {track_name} - {track_artists}')
            bot.send_chat_action(chat_id, 'typing')

            download_thread.join()

            mp3_filename = f'{temp_folder}/{track_name}.mp3'
            convert_to_mp3(f'{temp_folder}/{track_name}.ogg', mp3_filename)

            audio_file = open(mp3_filename, 'rb')
            bot.send_audio(chat_id, audio_file)

            # Cleanup - Delete the temporary folder
            delete_temp_folder(temp_folder)
        else:
            bot.send_message(chat_id, f"No preview available for: {track_name} - {track_artists}")
    except IndexError:
        bot.send_message(chat_id, f"No results found for: {query}")
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")


bot.polling()
