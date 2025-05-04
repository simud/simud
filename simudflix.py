import requests
from bs4 import BeautifulSoup

# ID dei film Marvel
movies = {
    "Iron Man": 312,
    "Iron Man 2": 313,
    "Iron Man 3": 314,
    "The Avengers": 315,
    "Captain America": 316,
    "Thor": 317,
    "Guardians of the Galaxy": 320,
    "Doctor Strange": 322,
    "Black Panther": 325,
    "Avengers: Endgame": 328
}

headers = {
    "User-Agent": "Mozilla/5.0"
}

m3u_entries = []

for title, id_ in movies.items():
    url = f"https://streamingcommunity.spa/watch/{id_}"
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"Errore nel caricare la pagina per l'ID {id_}: {res.status_code}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        scripts = soup.find_all("script")
        found = False

        for script in scripts:
            if script.string and ".m3u8" in script.string:
                start = script.string.find("https")
                end = script.string.find(".m3u8", start)
                if start != -1 and end != -1:
                    m3u_url = script.string[start:end + 5]
                    m3u_entries.append(f"#EXTINF:-1,{title}\n{m3u_url}")
                    found = True
                    break

        if not found:
            print(f"Flusso M3U8 non trovato per l'ID {id_} nella pagina.")

    except Exception as e:
        print(f"Errore per l'ID {id_}: {e}")

with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    f.write("\n".join(m3u_entries))

print("File streaming.m3u8 creato.")