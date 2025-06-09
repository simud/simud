import requests
import re
import os

# URL della playlist originale
playlist_url = "https://raw.githubusercontent.com/simud/simud/refs/heads/main/skystreaming_playlist.m3u8"

# Configurazioni per EXTVLCOPT e logo
user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
logo_url = "https://www.davidemaggio.it/app/uploads/2021/08/business.jpg"

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
    m3u8_pattern = r'https?://[^\s"]+\.m3u8'
    match = re.search(m3u8_pattern, embed_page)
    return match.group(0) if match else None

# Funzione per estrarre il nome del canale e il group-title dalla riga EXTINF
def extract_channel_info(extinf_line):
    group_match = re.search(r'group-title="([^"]+)"', extinf_line)
    group_title = group_match.group(1) if group_match else "Senza Gruppo"
    name_match = re.search(r',(.+)$', extinf_line)
    channel_name = name_match.group(1).strip() if name_match else "Canale Sconosciuto"
    return group_title, channel_name

# Funzione per estrarre dinamicamente embed_base_url, referrer e origin dalla playlist
def extract_dynamic_urls(playlist_content):
    # Cerca un URL nella playlist per dedurre referrer e origin (es. https://skystreaming.stream)
    url_pattern = r'(https?://[^\s/]+)'
    url_matches = re.findall(url_pattern, playlist_content)
    
    # Cerca un dominio che contenga "skystreaming.stream" o simile
    target_domain = None
    for url in url_matches:
        if "skystreaming.stream" in url:
            target_domain = url
            break
    
    if target_domain:
        referrer = target_domain
        origin = target_domain
    else:
        print("Dominio skystreaming.stream non trovato nella playlist, utilizzo fallback.")
        referrer = "https://skystreaming.yoga"
        origin = "https://skystreaming.yoga"

    # Cerca un URL di embed per dedurre embed_base_url
    embed_pattern = r'(https?://[^\s/]+/embed/[^\s]+)'
    embed_match = re.search(embed_pattern, playlist_content)
    
    if embed_match:
        embed_url = embed_match.group(1)
        embed_base_domain = re.match(r'(https?://[^\s/]+)', embed_url).group(1)
        embed_base_url = f"{embed_base_domain}/embed/"
    else:
        print("Impossibile estrarre embed_base_url, utilizzo valore di fallback.")
        embed_base_url = f"{referrer}/embed/"

    return embed_base_url, referrer, origin

# Funzione principale
def create_new_m3u8():
    # Scarica la playlist originale
    playlist_content = fetch_url(playlist_url)
    if not playlist_content:
        print("Impossibile scaricare la playlist originale.")
        return

    # Estrai dinamicamente embed_base_url, referrer e origin
    embed_base_url, referrer, origin = extract_dynamic_urls(playlist_content)
    print(f"Utilizzo: embed_base_url={embed_base_url}, referrer={referrer}, origin={origin}")

    # Percorso per il file di output
    output_path = "skystream.m3u8"
    new_playlist_lines = ["#EXTM3U"]

    # Variabili per processare la playlist
    current_info = None
    embed_pattern = r'https?://[^\s/]+/embed/([^\s]+)'

    # Processa la playlist riga per riga
    for line in playlist_content.splitlines():
        if line.startswith("#EXTINF:"):
            current_info = line
        elif line.startswith("http") and "/embed/" in line:
            embed_match = re.search(embed_pattern, line)
            if embed_match and current_info:
                embed_code = embed_match.group(1)
                embed_url = f"{embed_base_url}{embed_code}"
                print(f"Processo embed: {embed_url}")
                
                embed_page = fetch_url(embed_url)
                if embed_page:
                    m3u8_url = extract_m3u8_stream(embed_page)
                    if m3u8_url:
                        group_title, channel_name = extract_channel_info(current_info)
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
