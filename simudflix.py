from scuapi import API
import re

# URL di base
base_url = "https://StreamingCommunity.spa"
sc = API(base_url)

# Lista dei film Marvel
film_marvel = [
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

# Header VLC
vlc_headers = f"""#EXTVLCOPT:http-referrer={base_url}/
#EXTVLCOPT:http-origin={base_url}
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1
"""

# File m3u8 di output
with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")

    for title in film_marvel:
        try:
            results = sc.search(title)
            if not results:
                print(f"Film non trovato: {title}")
                continue

            # Prendi il primo risultato
            movie_key = list(results.keys())[0]
            movie_id = results[movie_key]["id"]

            # Ottieni i link del film
            iframe, m3u_url, m3u_file = sc.get_links(movie_id, get_m3u=True)

            # Scegli il link m3u8 più "recente" se presente
            urls = re.findall(r'https[^\s&"]+token[^&"\']+', m3u_url)
            best_url = sorted(urls, reverse=True)[0] if urls else m3u_url

            f.write(f"#EXTINF:-1,{movie_key}\n")
            f.write(vlc_headers)
            f.write(f"{best_url}\n")
            print(f"Aggiunto: {movie_key}")

        except Exception as e:
            print(f"Errore con {title}: {e}")