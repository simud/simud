import os
from pytube import Channel

def create_m3u8(youtube_channel_url, output_file="highlights.m3u8"):
    try:
        # Ottieni i video dal canale
        channel = Channel(youtube_channel_url)
        print(f"Scaricando video dal canale: {channel.channel_name}")
        
        # Filtra gli ultimi 20 video che contengono "gol e highlights" nel titolo
        videos = [video for video in channel.videos if "gol e highlights" in video.title.lower()][:20]

        # Crea il file M3U8
        with open(output_file, "w", encoding="utf-8") as m3u8_file:
            m3u8_file.write("#EXTM3U\n")
            for video in videos:
                m3u8_file.write(f"#EXTINF:-1,logo={video.thumbnail_url},{video.title}\n")
                m3u8_file.write(f"{video.watch_url}\n")

        print(f"Playlist salvata in {output_file}")
    except Exception as e:
        print(f"Errore: {e}")

# URL del canale YouTube
youtube_channel_url = "https://youtube.com/@skysport"
create_m3u8(youtube_channel_url)