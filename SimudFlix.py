import logging
import cloudscraper
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def avvia_browser():
    options = Options()
    options.add_argument('--headless=new')  # Modalità headless moderna
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    return webdriver.Chrome(options=options)

def cerca_iframe(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        iframe = driver.find_element(By.TAG_NAME, "iframe")
        return iframe.get_attribute("src")
    except Exception as e:
        logging.error(f"Errore nel recupero dell'iframe per {url}: {e}")
        return None

def estrai_film():
    scraper = cloudscraper.create_scraper()
    driver = avvia_browser()

    url = "https://altadefinizione.locker/"
    response = scraper.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    film_links = soup.select("div.ml-item > a")[:5]  # estrae solo i primi 5 film per esempio
    m3u8_urls = []

    for link in film_links:
        titolo = link.get("title", "").strip()
        url_film = link.get("href")
        logging.info(f"Titolo pulito: {titolo}")
        logging.info(f"Caricamento della pagina del film: {url_film}")
        iframe_url = cerca_iframe(driver, url_film)
        if iframe_url:
            m3u8_urls.append(f"# {titolo}\n{iframe_url}")

    driver.quit()

    with open("films.m3u8", "w", encoding="utf-8") as f:
        f.write("\n\n".join(m3u8_urls))

if __name__ == "__main__":
    estrai_film()
