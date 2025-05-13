import requests
from bs4 import BeautifulSoup
import re
import m3u8

# Intestazioni per simulare un browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# URL della homepage
base_url = "https://www.fullreplays.com/"

def get_event_links():
    """Estrae i link agli eventi dalla homepage."""
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cerca link agli eventi (es. articoli o pagine di replay)
        event_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if '/20' in href or 'match' in href.lower() or 'replay' in href.lower():
                if href.startswith('/'):
                    href = base_url.rstrip('/') + href
                event_links.append(href)
        
        return list(set(event_links))  # Rimuove duplicati
    except Exception as e:
        print(f"Errore durante l'estrazione dei link: {e}")
        return []

def find_m3u8_urls(event_url):
    """Cerca URL di file M3U8 nella pagina di un evento."""
    try:
        response = requests.get(event_url, headers=headers)
        response.raise_for_status()
        
        # Cerca direttamente nei contenuti della pagina
        m3u8_urls = re.findall(r'https?://[^\s\'"]+\.m3u8', response.text)
        
        # Se non trova nulla, cerca in iframe o script dinamici
        if not m3u8_urls:
            soup = BeautifulSoup(response.text, 'html.parser')
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src', '')
                if src:
                    try:
                        iframe_response = requests.get(src, headers=headers)
                        m3u8_urls.extend(re.findall(r'https?://[^\s\'"]+\.m3u8', iframe_response.text))
                    except:
                        continue
        
        return list(set(m3u8_urls))
    except Exception as e:
        print(f"Errore durante l'analisi di {event_url}: {e}")
        return []

def create_m3u8_playlist(m3u8_urls, output_file="replays.m3u8"):
    """Crea un file M3U8 con i flussi trovati."""
    playlist = m3u8.M3U8()
    
    for url in m3u8_urls:
        # Aggiunge ogni flusso come una variante
        stream = m3u8.Media(uri=url, media_type='VIDEO', name=url.split('/')[-1])
        playlist.media.append(stream)
    
    # Salva il file M3U8
    with open(output_file, 'w') as f:
        f.write(playlist.dumps())
    print(f"File M3U8 salvato come {output_file}")

def main():
    # Trova i link agli eventi
    print("Estrazione dei link agli eventi...")
    event_links = get_event_links()
    
    if not event_links:
        print("Nessun link agli eventi trovato.")
        return
    
    # Cerca flussi M3U8 in ogni pagina evento
    all_m3u8_urls = []
    for link in event_links:
        print(f"Analisi di {link}...")
        m3u8_urls = find_m3u8_urls(link)
        all_m3u8_urls.extend(m3u8_urls)
    
    if all_m3u8_urls:
        print("Flussi M3U8 trovati:", all_m3u8_urls)
        create_m3u8_playlist(all_m3u8_urls)
    else:
        print("Nessun flusso M3U8 trovato.")

if __name__ == "__main__":
    main()
