from streamingcommunity_unofficialapi import API
import os
from urllib.parse import urlparse

movies = [
    "Thunderbolts",
    "Iron Man 3",
    "Spider-Man: No Way Home",
    "Black Panther: Wakanda Forever",
    "Captain America: Civil War",
    "Thor: Ragnarok",
    "Doctor Strange",
    "Avengers: Endgame",
    "Ant-Man and The Wasp",
    "Guardians of the Galaxy Vol. 3"
]

output_file = os.path.join(os.getenv("GITHUB_WORKSPACE", "."), "streaming.m3u8")
api = API()
lines = ["#EXTM3U\n"]

for movie in movies:
    try:
        results = api.search(movie)
        best_match = list(results.values())[0]
        movie_id = best_match["id"]
        title = api.get_title(movie_id)

        if not title.streams:
            print(f"Nessun flusso trovato per {movie}")
            continue

        # Scegli il flusso più recente (in base a created_at o ultima stagione/episodio)
        sorted_streams = sorted(title.streams, key=lambda x: x.get("created_at", ""), reverse=True)
        best_stream = sorted_streams[0]

        stream_url = best_stream["url"]
        parsed = urlparse(api.base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        lines.append(f"#EXTINF:-1,{movie}")
        lines.append(f"#EXTVLCOPT:http-referrer={origin}")
        lines.append(f"#EXTVLCOPT:http-origin={origin}")
        lines.append("#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
        lines.append(stream_url + "\n")

    except Exception as e:
        print(f"Errore con {movie}: {e}")

with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("File streaming.m3u8 aggiornato.")