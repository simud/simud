import requests
from streamingcommunity_unofficialapi import StreamingCommunity
import random

# Lista di 10 film Marvel scelti
film_selezionati = [
    "Thunderbolts",
    "Guardiani della Galassia Vol. 3",
    "Avengers: Endgame",
    "Black Panther: Wakanda Forever",
    "Doctor Strange nel Multiverso della Follia",
    "Spider-Man: No Way Home",
    "Shang-Chi e la Leggenda dei Dieci Anelli",
    "Eternals",
    "Ant-Man and the Wasp: Quantumania",
    "Captain Marvel"
]

# Funzione per generare un user-agent casuale
def genera_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"
    ]
    return random.choice(user_agents)

# Funzione per generare un referer casuale
def genera_referer():
    referers = [
        "https://streamingcommunity.spa",
        "https://streamingcommunity.spa/watch",
        "https://streamingcommunity.spa/movie"
    ]
    return random.choice(referers)

# Inizializzare la libreria StreamingCommunity
sc = StreamingCommunity()

# File M3U8 da generare
m3u8_filename = "streaming.m3u8"
with open(m3u8_filename, "w") as m3u8_file:
    m3u8_file.write("#EXTM3U\n")  # Intestazione del file M3U8

    # Loop per ogni film nella lista
    for film in film_selezionati:
        print(f"Recuperando flusso per {film}...")
        
        # Recupera le informazioni del film (modifica in base alla libreria)
        try:
            flussi = sc.get_film_streams(film)  # Questa è una chiamata esemplificativa, verifica nella libreria per il nome corretto
            if not flussi:
                print(f"Nessun flusso trovato per {film}.")
                continue

            # Scegli un flusso (esempio: il primo disponibile)
            flusso = flussi[0]  # Potresti fare altre scelte in base a qualità, tipo, ecc.

            # Prepara i dati per la richiesta HTTP con referer e user agent
            headers = {
                "User-Agent": genera_user_agent(),
                "Referer": genera_referer()
            }
            
            # Ottieni il link del flusso (modifica in base alla struttura della libreria)
            url_flusso = flusso["url"]

            # Scrivi il flusso nel file M3U8
            m3u8_file.write(f"#EXTINF:-1,{film}\n{url_flusso}\n")

            print(f"Flusso per {film} aggiunto al M3U8.")
        
        except Exception as e:
            print(f"Errore nel recupero del flusso per {film}: {e}")

print(f"File {m3u8_filename} creato con successo.")