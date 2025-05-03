from fastapi import FastAPI, Response
from scuapi import API

app = FastAPI()

# Dominio attuale di StreamingCommunity
BASE_DOMAIN = "streamingcommunity.spa"
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

@app.get("/")
def root():
    return {"message": "StreamingCommunity M3U8 API attiva"}

@app.get("/playlist.m3u8")
def generate_playlist():
    user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
    ref_and_origin = BASE_URL

    playlist_entries = ["#EXTM3U"]

    for film in film_lista:
        try:
            results = sc.search(film)
            match = next((k for k in results if film.lower() in k.lower()), None)
            if not match:
                continue

            movie_id = results[match]["id"]
            _, m3u_url, _ = sc.get_links(movie_id, get_m3u=True)

            playlist_entries.append(
                f'#EXTINF:-1,{match}\n'
                f'#EXTVLCOPT:http-referrer={ref_and_origin}\n'
                f'#EXTVLCOPT:http-origin={ref_and_origin}\n'
                f'#EXTVLCOPT:http-user-agent={user_agent}\n'
                f'{m3u_url}'
            )
        except Exception as e:
            print(f"Errore con {film}: {e}")
            continue

    playlist_str = "\n".join(playlist_entries)
    return Response(content=playlist_str, media_type="application/x-mpegURL")