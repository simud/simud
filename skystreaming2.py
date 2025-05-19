import requests
import re
import os

# URL della playlist originale
playlist_url = "https://raw.githubusercontent.com/simud/simud/refs/heads/main/skystreaming_playlist.m3u8"
# Base URL per gli embed
embed_base_url = "https://skystreaming.help/embed/"

# Configurazioni per EXTVLCOPT e logo
user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
referrer = "https://skystreaming.help"
origin = "https://skystreaming.help"
logo_url = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

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

# Funzione per estrarre il nome del canale e il group-title dalla riga EXTINF
def extract_channel_info(extinf_line):
    # Estrae il group-title
    group_match = re.search(r'group-title="([^"]+)"', extinf_line)
    group_title = group_match.group(1) if group_match else "Senza Gruppo"
    # Estrae il nome del canale dopo la virgola
    name_match = re.search(r',(.+)$', extinf_line)
    channel_name = name_match.group(1).strip() if name_match else "Canale Sconosciuto"
    return group_title, channel_name

# Funzione principale
def create_new_m3u8():
    # Scarica la playlist originale
    playlist_content = fetch_url(playlist_url)
    if not playlist_content:
        print("Impossibile scaricare la playlist originale.")
        return

    # Percorso per il file di output
    output_path = "skystream.m3u8"
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
            if embed_match and current_info:
                embed_code = embed_match.group(1)
                embed_url = f"https://skystreaming.help/embed/{embed_code}"
                print(f"Processo embed: {embed_url}")
                
                # Accedi alla pagina embed
                embed_page = fetch_url(embed_url)
                if embed_page:
                    # Estrai il flusso m3u8
                    m3u8_url = extract_m3u8_stream(embed_page)
                    if m3u8_url:
                        # Estrai group-title e nome del canale
                        group_title, channel_name = extract_channel_info(current_info)
                        # Crea la struttura richiesta
                        new_playlist_lines.append(
                            f'#EXTINF:-1 group-title="{group_title}" tvg-logo="{logo_url}",{channel_name}'
                        )
                        new_playlist_lines.append(f'#EXTVLCOPT:http-user-agent={user_agent}')
                        new_playlist_lines.append(f'#EXTVLCOPT:http-referrer={referrer}')
                        new_playlist_lines.append(f'#EXTVLCOPT:http-origin={origin}')
                        new_playlist_lines.append(m3u8_url)
                        print(f"Flusso trovato per {channel_name} (Gruppo: {group_title}): {m3u8_url}")
                    else:
                        print(f"Nessun flusso m3u8 trovato per {embed_url}")
                else:
                    print(f"Impossibile accedere a {embed_url}")
            else:
                print(f"Embed non valido o EXTINF mancante: {line}")
        else:
            # Ignora altre righe non rilevanti
            continue

    # Scrivi la nuova playlist
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_playlist_lines) + "\n")
        print(f"Nuova playlist creata: {output_path}")
    except Exception as e:
        print(f"Errore nella scrittura del file: {e}")

if __name__ == "__main__":
    create_new_m3u8()
