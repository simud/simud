import requests
import re
import os
import subprocess
from bs4 import BeautifulSoup

# URL di partenza (homepage o pagina con elenco eventi)
base_url = "https://skystreaming.onl/"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://skystreaming.onl",
    "Referer": "https://skystreaming.onl/"
}

# Percorso della repository locale
repo_path = os.path.expanduser("~/simud")  # Assicurati che il percorso sia corretto
file_path = os.path.join(repo_path, "skystreaming_playlist.m3u")

# Funzione per trovare i link alle pagine evento
def find_event_pages():
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        event_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.match(r'/view/[^/]+/[^/]+', href):
                full_url = base_url + href.lstrip('/')
                event_links.add(full_url)
            elif re.match(r'https://skystreaming\.onl/view/[^/]+/[^/]+', href):
                event_links.add(href)

        return list(event_links)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine evento: {e}")
        return []

# Funzione per estrarre il flusso video da una pagina evento
def get_video_stream(event_url):
    try:
        response = requests.get(event_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src and re.search(r'\.(m3u8|mp4|ts|html|php)', src, re.IGNORECASE):
                return src, iframe

        return None, None

    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {event_url}: {e}")
        return None, None

# Funzione per estrarre il nome del canale
def extract_channel_name(event_url):
    event_name_match = re.search(r'/view/([^/]+)/[^/]+', event_url)
    if event_name_match:
        return event_name_match.group(1).replace('-', ' ').title()
    return "Unknown Channel"

# Funzione per creare il file M3U
def create_m3u_file(video_streams):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        groups = {}
        for event_url, stream_url in video_streams:
            if not stream_url:
                continue
            channel_name = extract_channel_name(event_url)
            group = "Sport" if "sport" in channel_name.lower() else "Eventi"
            
            if group not in groups:
                groups[group] = []
            groups[group].append((channel_name, stream_url))
        
        for group, channels in groups.items():
            channels.sort(key=lambda x: x[0].lower())
            for channel_name, link in channels:
                f.write(f"#EXTINF:-1 group-title=\"{group}\", {channel_name}\n")
                f.write(f"{link}\n")
    
    print(f"File M3U aggiornato: {file_path}")

# Funzione per eseguire commit e push su GitHub
def commit_and_push():
    try:
        os.chdir(repo_path)
        subprocess.run(["git", "add", "skystreaming_playlist.m3u"], check=True)
        subprocess.run(["git", "commit", "-m", "Aggiornata playlist M3U"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Modifiche pushate con successo alla repository.")
    except subprocess.CalledProcessError as e:
        print(f"Errore durante il commit/push: {e}")

# Esegui lo script
if __name__ == "__main__":
    event_pages = find_event_pages()
    video_streams = [(url, get_video_stream(url)[0]) for url in event_pages if get_video_stream(url)[0]]
    
    if video_streams:
        create_m3u_file(video_streams)
        commit_and_push()
    else:
        print("Nessun flusso video trovato.")

        if video_streams:
            create_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
