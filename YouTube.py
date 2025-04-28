import os
from telegram import Bot, TelegramError

# Configura il bot Telegram
bot_token = '7739304539:AAGgb6vS9647L5cROt_5CLX7_MkM37dD8DM'
channel_username = '@nome_canale'  # Modifica con il nome del canale

def get_channel_id(bot, channel_username):
    """Ottiene l'ID del canale Telegram."""
    try:
        chat = bot.get_chat(channel_username)
        return chat.id
    except TelegramError as e:
        print(f"Errore durante il recupero dell'ID del canale: {e}")
        return None

def fetch_last_videos(bot, channel_id, limit=20):
    """Scarica gli ultimi video da un canale Telegram."""
    try:
        messages = bot.get_chat_history(chat_id=channel_id, limit=limit)
        video_urls = []
        for message in messages:
            if message.video:
                file_id = message.video.file_id
                file_info = bot.get_file(file_id)
                video_urls.append(f"https://api.telegram.org/file/bot{bot_token}/{file_info.file_path}")
        return video_urls
    except TelegramError as e:
        print(f"Errore durante il recupero dei video: {e}")
        return []

def generate_m3u8(video_urls, output_file='telegram.m3u8'):
    """Genera un file M3U8 con i link ai video."""
    with open(output_file, 'w') as f:
        f.write("#EXTM3U\n")
        for url in video_urls:
            f.write("#EXTINF:-1,\n")
            f.write(f"{url}\n")

if __name__ == "__main__":
    bot = Bot(token=bot_token)
    
    # Passo 1: Ottieni l'ID del canale
    channel_id = get_channel_id(bot, channel_username)
    if channel_id is None:
        print("Errore: impossibile ottenere l'ID del canale.")
    else:
        print(f"ID del canale: {channel_id}")
        
        # Passo 2: Scarica gli ultimi video
        video_urls = fetch_last_videos(bot, channel_id)
        if video_urls:
            # Passo 3: Genera il file M3U8
            generate_m3u8(video_urls)
            print("File telegram.m3u8 generato con successo!")
        else:
            print("Nessun video trovato.")