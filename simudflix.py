from scuapi import API
import os

# Lista dei titoli che vuoi cercare
film_list = [
    "Iron Man 3",
    "Thor: Ragnarok",
    "Captain America: Civil War",
    "Black Panther: Wakanda Forever",
    "Spider-Man: No Way Home",
    "Doctor Strange nel Multiverso della Follia",
    "The Marvels"
]

api = API()
playlist_lines = ["#EXTM3U"]

for title in film_list:
    try:
        print(f"Cerco: {title}")
        results = api.search(title)
        if not results:
            print(f"Film non trovato: {title}")
            continue

        stream = api.get_stream(results[0]["id"])
        if stream and "m3u8" in stream:
            print(f"Flusso trovato per {title}")
            playlist_lines.append(f"#EXTINF:-1,{title}")
            playlist_lines.append(stream)
        else:
            print(f"Nessun flusso disponibile per {title}")

    except Exception as e:
        print(f"Errore per {title}: {e}")

# Scrive il file M3U8
with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("\n".join(playlist_lines))

print("File M3U8 generato correttamente.")