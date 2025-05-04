from scuapi import API

# Inizializza l'API con il dominio corretto
sc = API('streamingcommunity.spa')

# Lista di 10 film Marvel
marvel_movies = [
    "Iron Man",
    "The Incredible Hulk",
    "Thor",
    "Captain America: The First Avenger",
    "The Avengers",
    "Guardians of the Galaxy",
    "Doctor Strange",
    "Black Panther",
    "Captain Marvel",
    "Avengers: Endgame"
]

# Lista per memorizzare le voci M3U
m3u_entries = []

for movie in marvel_movies:
    try:
        # Ricerca del film
        results = sc.search(movie)
        if results:
            # Prende il primo risultato
            first_result = next(iter(results.values()))
            slug = first_result['slug']
            # Carica i dettagli del film
            details = sc.load(slug)
            # Estrae l'URL del flusso M3U8
            m3u8_url = details.get('m3u8_url')
            if m3u8_url:
                # Aggiunge l'entry al file M3U
                m3u_entries.append(f"#EXTINF:-1,{movie}\n{m3u8_url}")
            else:
                print(f"Flusso M3U8 non trovato per {movie}")
        else:
            print(f"Nessun risultato trovato per {movie}")
    except Exception as e:
        print(f"Errore durante l'elaborazione di {movie}: {e}")

# Scrive le voci nel file M3U con il nuovo nome
with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    f.write("\n".join(m3u_entries))

print("File streaming.m3u8 creato con successo.")