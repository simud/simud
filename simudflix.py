from streamingcommunity import API
from urllib.parse import urlparse
import os
import time

# Lista dei titoli da cercare
movies = [
    "Thunderbolts", "Iron Man 3", "Spider-Man: No Way Home",
    "Black Panther: Wakanda Forever", "Captain America: Civil War",
    "Thor: Ragnarok", "Doctor Strange", "Avengers: Endgame",
    "Ant-Man and The Wasp", "Guardians of the Galaxy Vol. 3"
]

# Base URL (senza schema https://)
base_url = "StreamingCommunity.spa"
sc = API(base_url)

m3u8_content = "#EXTM3U\n"

for movie in movies:
    try:
        results = sc.search(movie)
        if not results:
            print(f"Nessun risultato per {movie}")
            continue

        # Prendi il più recente (basato su 'last_air_date')
        most_recent = sorted(results.values(), key=lambda x: x.get("last_air_date", ""), reverse=True)[0]
        movie_id = most_recent["id"]

        streams = sc.get_streams(movie_id)
        if not streams:
            print(f"Nessun flusso trovato per {movie}")
            continue

        # Prendi il primo flusso disponibile
        stream_url = list(streams.values())[0]

        parsed_url = urlparse(f"https://{base_url}")
        referer = f"{parsed_url.scheme}://{parsed_url.netloc}"

        m3u8_content += (
            f"#EXTINF:-1,{movie}\n"
            f"#EXTVLCOPT:http-referrer={referer}/\n"
            f"#EXTVLCOPT:http-origin={referer}\n"
            f"#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1\n"
            f"{stream_url}\n"
        )

        time.sleep(1)  # Limita le richieste
    except Exception as e:
        print(f"Errore con {movie}: {e}")

# Scrive tutti i flussi in un singolo file
with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write(m3u8_content)