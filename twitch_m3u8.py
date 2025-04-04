import streamlink
import os
from pathlib import Path

# Lista dei profili Twitch da controllare
twitch_profiles = [
    "https://www.twitch.tv/therealmarzaa",
    "https://www.twitch.tv/manuuxo"
]

# Percorso del file M3U8 (root del repository, non desktop)
m3u8_file = Path("twitch_streams.m3u8")

# User-Agent specifico
user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"

# Inizio del contenuto del file M3U8
m3u8_content = "#EXTM3U\n"

# Funzione per ottenere il flusso da un profilo Twitch
def get_stream_url(twitch_url):
    try:
        streams = streamlink.streams(twitch_url)
        if streams:
            # Prendi la qualità "best" disponibile
            stream = streams["best"]
            return stream.url
        else:
            return None
    except Exception as e:
        print(f"Errore con {twitch_url}: {e}")
        return None

# Ciclo sui profili
for profile in twitch_profiles:
    stream_url = get_stream_url(profile)
    if stream_url:
        # Aggiungi il flusso al file M3U8 con il formato richiesto
        channel_name = profile.split('/')[-1]
        m3u8_content += f"#EXTINF:-1, {channel_name}\n"
        m3u8_content += f"#EXTVLCOPT:http-referrer={profile}\n"
        m3u8_content += f"#EXTVLCOPT:http-origin={profile}\n"
        m3u8_content += f"#EXTVLCOPT:http-user-agent={user_agent}\n"
        m3u8_content += f"{stream_url}\n"
    else:
        print(f"Nessun flusso attivo per {profile}")

# Scrivi il file M3U8 nella root del repository
with open(m3u8_file, "w") as f:
    f.write(m3u8_content)

print(f"File M3U8 creato: {m3u8_file}")
