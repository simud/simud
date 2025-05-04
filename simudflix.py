import requests
from bs4 import BeautifulSoup
import m3u8
import subprocess

# URL della pagina di streaming
url = 'https://streamingcommunity.spa/watch/314'

# 1. Recupera il codice sorgente della pagina
response = requests.get(url)
html_content = response.text

# 2. Analizza il contenuto HTML per trovare il link m3u8
soup = BeautifulSoup(html_content, 'html.parser')

# Supponiamo che l'URL del flusso m3u8 sia in un tag <script> o <video>
# Adatta questa parte in base a dove si trova effettivamente l'URL m3u8 nella pagina HTML
m3u8_url = None
for script in soup.find_all('script'):
    if 'm3u8' in script.text:
        # Trova il link m3u8 nel contenuto del tag <script>
        m3u8_url = script.text.split('m3u8')[1].split('"')[1]  # Estrai l'URL
        break

if not m3u8_url:
    print("Non trovato flusso m3u8 nella pagina")
else:
    print(f"Flusso m3u8 trovato: {m3u8_url}")

    # 3. Scarica e salva il flusso usando ffmpeg
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', m3u8_url,  # Inserisci l'URL del flusso m3u8
        '-c', 'copy',     # Copia senza ricodifica
        '-bsf:a', 'aac_adtstoasc',  # Correzione del formato audio
        'output.mp4'      # Nome del file finale
    ]
    subprocess.run(ffmpeg_cmd)