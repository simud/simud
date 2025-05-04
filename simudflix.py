import requests
from bs4 import BeautifulSoup

# URL della pagina contenente il flusso
url = "https://streamingcommunity.spa/watch/314"

# Effettua la richiesta HTTP alla pagina
response = requests.get(url)
response.raise_for_status()

# Analizza il contenuto HTML della pagina
soup = BeautifulSoup(response.text, 'html.parser')

# Cerca il link del flusso M3U8 nella pagina
# Adatta questa parte in base alla struttura della pagina
# Questo è solo un esempio, potrebbe essere necessario fare una ricerca più accurata
m3u8_url = None

# Supponiamo che il flusso M3U8 sia in un attributo "data-m3u8" o simile
# Esplora l'HTML della pagina per determinare come ottenere il link esatto

# Esempio di ricerca tramite tag script (spesso i flussi M3U8 sono incorporati in script JS)
for script in soup.find_all('script'):
    if 'm3u8' in script.text:
        # Estrai l'URL del flusso M3U8 dal testo JavaScript (questa parte può variare)
        start_index = script.text.find("m3u8")
        end_index = script.text.find(".m3u8") + 5
        m3u8_url = script.text[start_index:end_index]
        break

if m3u8_url:
    print(f"Flusso M3U8 trovato: {m3u8_url}")
    
    # Crea una playlist M3U8
    playlist_filename = "streaming.m3u8"
    with open(playlist_filename, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write("#EXTINF:-1, Film Esempio\n")
        f.write(m3u8_url + "\n")

    print(f"Playlist creata con successo: {playlist_filename}")
else:
    print("Flusso M3U8 non trovato.")