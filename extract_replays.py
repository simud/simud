from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin

# URL di esempio
match_url = "https://www.fullreplays.com/italy/serie-a/bologna-vs-napoli-7-apr-2025/"  # Sostituisci con un URL valido

# Configura Selenium
options = Options()
options.add_argument("--headless")  # Esegui senza interfaccia grafica
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
driver = webdriver.Chrome(options=options)

# Funzione per estrarre i flussi video e l'immagine
def extract_streams_and_image(url):
    try:
        driver.get(url)
        time.sleep(5)  # Attendi il caricamento completo (incluso eventuale CAPTCHA)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Estrai il titolo della partita
        event_name = soup.find("h1").get_text(strip=True) if soup.find("h1") else "Unnamed Event"
        
        # Trova l'immagine
        image_tag = soup.find("img", {"class": "entry-thumb"}) or soup.find("img")
        image_url = urljoin(url, image_tag["src"]) if image_tag and "src" in image_tag.attrs else None
        
        # Cerca i flussi video
        streams = []
        for script in soup.find_all("script"):
            script_content = script.string
            if script_content:
                video_urls = re.findall(r'(https?://[^\s\'"]+\.(mp4|m3u8|mpd))', script_content)
                streams.extend([url[0] for url in video_urls])
        
        if not streams:
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.endswith((".mp4", ".m3u8", ".mpd")):
                    streams.append(urljoin(url, href))
        
        return event_name, streams, image_url
    
    except Exception as e:
        print(f"Errore: {e}")
        return None, None, None
    finally:
        driver.quit()

# Funzione per creare il file M3U8
def create_m3u8_file(event_name, streams, image_url, output_file="replaycalcio.m3u8"):
    with open(output_file, "w") as f:
        f.write("#EXTM3U\n")
        f.write(f"#EXTINF:-1 tvg-logo=\"{image_url}\" group-title=\"Replay Calcio\",{event_name}\n")
        for stream in streams:
            f.write(f"{stream}\n")
    print(f"File {output_file} creato con successo!")

# Main
def main():
    print(f"Tentativo di accesso a: {match_url}")
    event_name, streams, image_url = extract_streams_and_image(match_url)
    
    if not streams:
        print("Nessun flusso video trovato.")
        return
    
    print(f"Evento: {event_name}")
    print(f"Flussi trovati: {streams}")
    print(f"Immagine: {image_url}")
    
    create_m3u8_file(event_name, streams, image_url)

if __name__ == "__main__":
    main()
