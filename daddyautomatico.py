import requests
import os

# URL della playlist originale
url = "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/main/daddylive-channels.m3u8"

# URL delle immagini
image1 = "https://i.postimg.cc/Ss88rXcm/photo-2025-03-12-12-23-14.png"
image2 = "https://i.postimg.cc/NFGs2Ptq/photo-2025-03-12-12-36-48.png"

# Percorso del file nel repository
FILE_PATH = "daddy.m3u8"

# Ottieni il contenuto# Ottieni il contenuto del file m3u8
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

# Salva il file localmente
if found_italy:
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"File {FILE_PATH} creato/aggiornato localmente con successo")
else:
    print("Nessun canale del gruppo ITALY trovato nella playlist.")
