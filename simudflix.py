from scuapi import API

# Inizializza l'API con il dominio corretto
sc = API('streamingcommunity.spa')

# Lista di film Marvel con i rispettivi ID
marvel_movies = {
    "Iron Man": 312,
    "Iron Man 2": 313,
    "Iron Man 3": 314,
    "Thor": 317,
    "Captain America: The First Avenger": 316,
    "The Avengers": 315,
    "Guardians of the Galaxy": 320,
    "Doctor Strange": 322,
    "Black Panther": 325,
    "Avengers: Endgame": 328
}

m3u_entries = []

for title, movie_id in marvel_movies.items():
    try:
        # Carica i dettagli usando l'ID
        details = sc.load(str(movie_id))
        m3u8_url = details.get('m3u8_url')
        if m3u8_url:
            m3u_entries.append(f"#EXTINF:-1,{title}\n{m3u8_url}")
        else:
            print(f"Nessun flusso M3U8 trovato per {title}")
    except Exception as e:
        print(f"Errore durante l'elaborazione di {title}: {e}")

# Scrittura del file .m3u8
with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    f.write("\n".join(m3u_entries))

print("File streaming.m3u8 creato con successo.")