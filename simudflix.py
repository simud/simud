from streamingcommunity import StreamingCommunity
import time

# Imposta il dominio di StreamingCommunity (modifica se necessario)
domain = 'streamingcommunity.spa'

# Crea un'istanza della classe StreamingCommunity
sc = StreamingCommunity(domain)

# Lista di film da cercare
film_list = [
    "The Matrix", "John Wick", "Avengers: Endgame", "Titanic", "The Dark Knight",
    "Inception", "Spider-Man: No Way Home", "Joker", "The Lion King", "Interstellar"
]

# Lista per memorizzare i link M3U8
m3u8_links = []

# Funzione per ottenere i link m3u8
def get_m3u8_links(film_name):
    try:
        # Cerca il film
        result = sc.search(film_name)
        if result:
            film_id = result[0]['id']  # Prendi il primo film trovato
            print(f"Film trovato: {film_name}")

            # Ottieni i link (iframe e m3u8)
            links = sc.get_links(film_id)
            iframe = links.get('iframe', '')
            m3u_url = links.get('m3u8', '')

            if iframe and m3u_url:
                m3u8_links.append(f"#{film_name} - {iframe}\n{m3u_url}")
            else:
                print(f"Nessun link m3u8 trovato per: {film_name}")
        else:
            print(f"Film '{film_name}' non trovato.")
    except Exception as e:
        print(f"Errore durante la ricerca dei link per '{film_name}': {e}")

# Esegui la ricerca per ogni film
for film in film_list:
    get_m3u8_links(film)
    time.sleep(1)  # Ritardo tra le richieste per non sovraccaricare il server

# Scrivi i risultati in un file .m3u8
with open("streaming.m3u8", "w") as file:
    for link in m3u8_links:
        file.write(link + "\n")

print("File streaming.m3u8 creato con successo!")