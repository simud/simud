from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import os
import time
from urllib.parse import urljoin

# URL reale - Sostituisci con uno valido
match_url = "https://www.fullreplays.com/italy/serie-a/inter-vs-milan-1-mar-2025/"  # Aggiorna questo

# Configura Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
driver = webdriver.Chrome(options=options)

# Funzione per estrarre i flussi video e l'immagine
def extract_streams_and_image(url):
    try:
        driver.get(url)
        print(f"Pagina caricata: {url}")
        time.sleep(5)  # Attendi il caricamento
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        print(f"Contenuto iniziale (prime 500 righe): {driver.page_source[:500]}")
        
        # Estrai il titolo della partita
        event_name = soup.find("h1").get_text(strip=True) if soup.find("h1") else "Unnamed Event"
        
        # Trova l'immagine
        image_tag = soup.find("img", {"class": "entry-thumb"}) or soup.find("img")
        image_url = urljoin(url, image_tag["src"]) if image_tag and "src" in image_tag.attrs else None
        
        # Cerca pulsanti con un XPath più specifico
        wait = WebDriverWait(driver, 10)
        buttons = driver.find_elements(By.XPATH, "//button | //a | //div[contains(@class, 'button') or contains(@class, 'play') or contains(text(), 'Okru') or contains(text(), 'smoothpre') or contains(text(), 'cybervynx') or contains(text(), 'Download') or contains(text(), 'Full Match')]")
        streams = []
        
        for button in buttons:
            try:
                button_text = button.text.strip()
                button_tag = button.tag_name
                button_class = button.get_attribute("class")
                print(f"Trovato elemento: tag={button_tag}, testo='{button_text}', classe='{button_class}'")
                
                # Scorri fino all'elemento e attendi che sia cliccabile
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                wait.until(EC.element_to_be_clickable(button))
                button.click()
                print(f"Cliccato: '{button_text}'")
                time.sleep(3)  # Attendi il caricamento del player
                
                # Aggiorna il sorgente della pagina
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # Cerca flussi nei tag <script>
                for script in soup.find_all("script"):
                    script_content = script.string
                    if script_content:
                        video_urls = re.findall(r'(https?://[^\s\'"]+\.(mp4|m3u8|mpd))', script_content)
                        streams.extend([url[0] for url in video_urls])
                
                # Cerca flussi nei link
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if href.endswith((".mp4", ".m3u8", ".mpd")):
                        streams.append(urljoin(url, href))
                
                # Cerca iframe
                iframes = soup.find_all("iframe")
                for iframe in iframes:
                    iframe_src = iframe.get("src")
                    if iframe_src and any(ext in iframe_src for ext in [".mp4", ".m3u8", ".mpd"]):
                        streams.append(urljoin(url, iframe_src))
                    elif iframe_src:
                        driver.get(urljoin(url, iframe_src))
                        time.sleep(2)
                        iframe_soup = BeautifulSoup(driver.page_source, "html.parser")
                        for script in iframe_soup.find_all("script"):
                            if script.string:
                                video_urls = re.findall(r'(https?://[^\s\'"]+\.(mp4|m3u8|mpd))', script.string)
                                streams.extend([url[0] for url in video_urls])
                        driver.back()
                
            except Exception as e:
                print(f"Errore durante il clic su '{button_text}': {e}")
        
        streams = list(set(streams))
        return event_name, streams, image_url
    
    except Exception as e:
        print(f"Errore generale: {e}")
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
