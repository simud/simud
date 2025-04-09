import requests
import os
from github import Github  # Richiede 'pygithub' (`pip install pygithub`)

# Configurazione GitHub
GITHUB_TOKEN = "YOUR_PERSONAL_ACCESS_TOKEN"  # Sostituisci con il tuo token
REPO_NAME = "username/repository"  # Sostituisci con username/nome-repo
FILE_PATH = "daddy.m3u8"  # Percorso nel repository

# URL della playlist originale
url = "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/main/daddylive-channels.m3u8"

# URL delle immagini
image1 = "https://i.postimg.cc/Ss88rXcm/photo-2025-03-12-12-23-14.png"
image2 = "https://i.postimg.cc/NFGs2Ptq/photo-2025-03-12-12-36-48.png"

# Ottieni il contenuto del file m3u8
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
response = requests.get(url, headers=headers)
lines = response.text.splitlines()

# Variabili per il nuovo file
output_lines = ["#EXTM3U"]
found_italy = False
channel_count = 0

# Processa ogni riga
i = 0
while i < len(lines):
    line = lines[i]
    if '#EXTINF' in line and 'group-title="ITALY"' in line:
        found_italy = True
        logo_url = image1 if channel_count % 2 == 0 else image2
        if 'tvg-logo="' in line:
            start_idx = line.find('tvg-logo="')
            end_idx = line.find('"', start_idx + 10) + 1
            line = line[:start_idx] + f'tvg-logo="{logo_url}"' + line[end_idx:]
        else:
            comma_idx = line.rfind(',')
            if comma_idx != -1:
                line = line[:comma_idx] + f' tvg-logo="{logo_url}"' + line[comma_idx:]
            else:
                line = f'{line} tvg-logo="{logo_url}"'
        output_lines.append(line)
        channel_count += 1
        
        i += 1
        while i < len(lines) and not lines[i].startswith('http'):
            if lines[i].startswith('#EXT'):
                output_lines.append(lines[i])
            i += 1
        if i < len(lines) and lines[i].startswith('http'):
            output_lines.append(lines[i])
    i += 1

# Contenuto del file
content = '\n'.join(output_lines)

# Carica su GitHub
if found_italy:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        # Prova ad aggiornare il file esistente
        file = repo.get_contents(FILE_PATH)
        repo.update_file(FILE_PATH, "Aggiornamento daddy.m3u8", content, file.sha)
        print(f"File {FILE_PATH} aggiornato con successo su GitHub")
    except:
        # Se il file non esiste, crealo
        repo.create_file(FILE_PATH, "Creazione daddy.m3u8", content)
        print(f"File {FILE_PATH} creato con successo su GitHub")
else:
    print("Nessun canale del gruppo ITALY trovato nella playlist.")
