import requests
import subprocess
import time

# URL per l'API di LJ Downloader
API_URL = "http://localhost:9666/jsonrpc"  # L'API di LJ Downloader, predefinita sulla porta 9666

# Funzione per ottenere il flusso m3u8 da LJ Downloader
def get_m3u8_link_from_ljdownloader(url):
    # Payload per aggiungere il link all'elenco di download di LJ Downloader
    payload = {
        "method": "linkgrabber.addLinks",
        "params": [url],
        "id": 1
    }

    # Esegui la richiesta API
    response = requests.post(API_URL, json=payload)

    # Verifica la risposta
    if response.status_code == 200:
        data = response.json()
        for item in data.get('result', []):
            if 'm3u8' in item['url']:  # Verifica se il flusso è un m3u8
                print(f"Flusso m3u8 trovato: {item['url']}")
                return item['url']
    else:
        print("Errore nell'API di LJ Downloader")
        return None

# Funzione per scaricare il flusso m3u8 usando ffmpeg
def download_m3u8_stream(m3u8_url):
    # Esegui il comando ffmpeg per scaricare il flusso
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', m3u8_url,  # URL del flusso m3u8
        '-c', 'copy',     # Copia senza ricodifica
        '-bsf:a', 'aac_adtstoasc',  # Correzione del formato audio
        'output.mp4'      # Nome del file finale
    ]
    subprocess.run(ffmpeg_cmd)

# Main: ottieni il flusso m3u8 e avvia il download
if __name__ == '__main__':
    url = 'https://streamingcommunity.spa/watch/314'  # Inserisci il link della pagina da cui estrarre il flusso
    m3u8_link = get_m3u8_link_from_ljdownloader(url)
    
    if m3u8_link:
        print(f"Scaricando il flusso da: {m3u8_link}")
        download_m3u8_stream(m3u8_link)
    else:
        print("Non trovato il flusso m3u8.")