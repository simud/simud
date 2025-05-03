from scuapi import API

# Inizializzazione dell'API con il dominio StreamingCommunity
sc = API('streamingcommunity.spa')

# Lista di film da ricercare
film_list = [
    "The Matrix", "John Wick", "Avengers: Endgame", "Titanic", "The Dark Knight",
    "Inception", "Spider-Man: No Way Home", "Joker", "The Lion King", "Interstellar"
]

# Lista per contenere i link m3u8
m3u8_links = []

# Funzione per ottenere i link m3u8
def get_m3u8_links(film_name):
    try:
        result = sc.search(film_name)
        if result:
            film_id = list(result.keys())[0]  # Prendiamo il primo risultato
            iframe, m3u_playlist_url, m3u_playlist_file = sc.get_links(film_id, get_m3u=True)
            m3u8_links.append(f"#{film_name} - {iframe}\n{m3u_playlist_url}")
        else:
            print(f"Film '{film_name}' non trovato.")
    except Exception as e:
        print(f"Errore nel recuperare i link per '{film_name}': {e}")

# Eseguiamo la ricerca per ogni film nella lista
for film in film_list:
    get_m3u8_links(film)

# Creiamo il file .m3u8
with open("streaming.m3u8", "w") as file:
    for link in m3u8_links:
        file.write(link + "\n")

print("File streaming.m3u8 creato con successo!")