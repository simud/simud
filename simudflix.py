import requests
import subprocess
import time

API_URL = "http://localhost:9666/jsonrpc"

# Funzione per ottenere il flusso m3u8 da LJ Downloader
def get_m3u8_link_from_ljdownloader(url):
    payload = {
        "method": "linkgrabber.addLinks",
        "params": [url],
        "id": 1
    }

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()  # Verifica se la risposta è ok (200)

        if response.status_code == 200:
            data = response.json()
            for item in data.get('result', []):
                if 'm3u8' in item['url']:
                    print(f"Flusso m3u8 trovato: {item['url']}")
                    return item['url']
        else:
            print(f"Errore nella risposta dell'API: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Errore di connessione all'API di LJ Downloader: {e}")
        return None

# Funzione per scaricare il flusso m3u8 usando ffmpeg
def download_m3u8_stream(m3u8_url):
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', m3u8_url,
        '-c', 'copy',
        '-bsf:a', 'aac_adtstoasc',
        'output.mp4'
    ]
    subprocess.run(ffmpeg_cmd)

if __name__ == '__main__':
    url = 'https://streamingcommunity.spa/watch/314'
    m3u8_link = get_m3u8_link_from_ljdownloader(url)
    
    if m3u8_link:
        print(f"Scaricando il flusso da: {m3u8_link}")
        download_m3u8_stream(m3u8_link)
    else:
        print("Non trovato il flusso m3u8.")