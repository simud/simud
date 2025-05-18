import requests
import re
import os
from urllib.parse import urljoin

# URL della playlist originale
playlist_url = "https://raw.githubusercontent.com/simud/simud/refs/heads/main/skystreaming_playlist.m3u8"
# Base URL per gli embed
embed_base_url = "view-source:https://skystreaming.help/embed/"

# Funzione per scaricare il contenuto di una URL
def fetch_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Errore nel recupero di {url}: {e}")
        return None

# Funzione per estrarre il flusso m3u8 dalla pagina embed
def extract_m3u8_stream(embed_page):
    if not embed_page:
        return None
    # Cerca un URL m3u8 nel testo della pagina
    m3u8_pattern = r'https?://[^\s"]+\.m3u8'
    match = re.search(m3u8_pattern, embed_page)
    return match.group(0) if match else None

# Funzione principale
def create_new_m3u8():
    # Scarica la playlist originale
    playlist_content = fetch_url(playlist_url)
    if not playlist_content:
        print("Impossibile scaricare la playlist originale.")
        return

    # Percorso per il file di output sul desktop
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "new_playlist.m3u8")
    new_playlist_lines = ["#EXTM3U"]  # Inizia con l'intestazione M3U

    # Variabili per processare la playlist
    current_info = None
    embed_pattern = r'https?://skystreaming\.help/embed/([^\s]+)'

    # Processa la playlist riga per riga
    for line in playlist_content.splitlines():
        if line.startswith("#EXTINF:"):
            current_info = line  # Salva la riga EXTINF
        elif line.startswith("http") and "skystreaming.help/embed/" in line:
            # Trovato un embed
            embed_match = re.search(embed_pattern, line)
            if embed_match:
                embed_code = embed_match.group(1)
                embed_url = f"https://skystreaming.help/embed/{embed_code}"
                print(f"Processo embed: {embed_url}")
                
                # Accedi alla pagina embed
                embed_page = fetch_url(embed_url)
                if embed_page:
                    # Estrai il flusso m3u8
                    m3u8_url = extract_m3u8_stream(embed_page)
                    if m3u8_url:
                        # Aggiungi alla nuova playlist
                        new_playlist_lines.append(current_info)
                        new_playlist_lines.append(m3u8_url)
                        print(f"Flusso trovato: {m3u8_url}")
                    else:
                        print(f"Nessun flusso m3u8 trovato per {embed_url}")
                else:
                    print(f"Impossibile accedere a {embed_url}")
            else:
                print(f"Embed non valido: {line}")
        else:
            # Mantieni le righe non embed (es. commenti o altro)
            if line and not line.startswith("#EXTINF:"):
                new_playlist_lines.append(line)

    # Scrivi la nuova playlist sul desktop
    try:
        with open(desktop_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_playlist_lines) + "\n")
        print(f"Nuova playlist creata: {desktop_path}")
    except Exception as e:
        print(f"Errore nella scrittura del file: {e}")

if __name__ == "__main__":
    create_new_m3u8()
