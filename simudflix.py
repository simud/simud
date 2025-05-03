import os
from scuapi import API

# Sito corrente di StreamingCommunity
BASE_DOMAIN = "StreamingCommunity.spa"
sc = API(BASE_DOMAIN)

# Lista di film Marvel in italiano
film_lista = [
    "Thunderbolts",
    "Iron Man 3",
    "Thor: Ragnarok",
    "Captain America: Civil War",
    "Black Panther: Wakanda Forever",
    "Spider-Man: No Way Home",
    "Doctor Strange nel Multiverso della Follia",
    "Avengers: Endgame",
    "Guardiani della Galassia Vol. 3",
    "The Marvels"
]

playlist_entries = []

for film in film_lista:
    results = sc.search(film)
    match = next((k for k in results.keys() if film.lower() in k.lower()), None)
    if not match:
        print(f"Film non trovato: {film}")
        continue

    movie_id = results[match]["id"]

    try:
        _, m3u_url, _ = sc.get_links(movie_id, get_m3u=True)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        referer = f"https://{BASE_DOMAIN}/titles/{movie_id}-{results[match]['slug']}"
        playlist_entries.append(
            f'#EXTINF:-1,{match}\n#EXTVLCOPT:http-user-agent={user_agent}\n#EXTVLCOPT:http-referrer={referer}\n{m3u_url}'
        )
        print(f"Aggiunto: {match}")
    except Exception as e:
        print(f"Errore per {film}: {e}")

# Scrive tutto in un unico file .m3u8
with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    f.write("\n".join(playlist_entries))

print("streaming.m3u8 generato correttamente.")