import os
from scuapi import API

# Dominio corrente
BASE_DOMAIN = "StreamingCommunity.spa"
BASE_URL = f"https://{BASE_DOMAIN}"
sc = API(BASE_DOMAIN)

# Lista dei film da cercare
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
    match = next((k for k in results if film.lower() in k.lower()), None)
    if not match:
        print(f"Film non trovato: {film}")
        continue

    movie_id = results[match]["id"]

    try:
        # Estrai i link del flusso in modo più preciso
        _, m3u_url, _ = sc.get_links(movie_id, get_m3u=True)

        # Verifica che il flusso contenga la giusta URL
        if "vixcloud.co" in m3u_url:
            # Rivediamo la struttura per includere correttamente l'header
            user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
            ref_and_origin = BASE_URL  # stesso valore per referer e origin

            # Aggiungi il flusso alla playlist
            playlist_entries.append(
                f'#EXTINF:-1,{match}\n'
                f'#EXTVLCOPT:http-referrer={ref_and_origin}\n'
                f'#EXTVLCOPT:http-origin={ref_and_origin}\n'
                f'#EXTVLCOPT:http-user-agent={user_agent}\n'
                f'{m3u_url}'
            )

            print(f"Aggiunto: {match} con URL: {m3u_url}")
        else:
            print(f"URL non valido per il film: {film}")

    except Exception as e:
        print(f"Errore per {film}: {e}")

# Scrive l'intera playlist in un unico file .m3u8
with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    f.write("\n".join(playlist_entries))

print("File streaming.m3u8 generato correttamente.")