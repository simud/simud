from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Imposta l'URL della home page
BASE_URL = "https://streamingcommunity.spa"

# Configura Selenium
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Esegui in modalità headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service("chromedriver")  # Sostituisci con il path del tuo ChromeDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Ottieni tutti i collegamenti dalla home page
def get_all_links(driver):
    driver.get(BASE_URL)
    time.sleep(5)  # Attendi il caricamento completo della pagina
    links = []
    elements = driver.find_elements(By.TAG_NAME, "a")  # Trova tutti i tag <a>
    for el in elements:
        href = el.get_attribute("href")
        if href:  # Assicurati che il collegamento non sia vuoto
            links.append(href)
    return list(set(links))  # Rimuove duplicati

# Salva i collegamenti in un file m3u8
def save_links_to_file(links, filename="streaming.m3u8"):
    with open(filename, "w") as file:
        for link in links:
            file.write(f"{link}\n")
    print(f"Collegamenti salvati in {filename}")

# Funzione principale
def main():
    driver = setup_driver()
    try:
        print(f"Apertura del sito: {BASE_URL}")
        links = get_all_links(driver)
        print(f"Collegamenti trovati ({len(links)}):")
        for link in links:
            print(link)
        save_links_to_file(links)  # Salva i collegamenti in streaming.m3u8
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
