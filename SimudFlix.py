from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

# Lista dei titoli Marvel da elaborare
marvel_links = [
    ("Iron Man", "https://altadefinizione.taipei/azione/1752-iron-man-1-streaming.html"),
    ("The Avengers", "https://altadefinizione.taipei/azione/1234-the-avengers-streaming.html"),
    ("Captain America: Civil War", "https://altadefinizione.taipei/azione/5678-captain-america-civil-war-streaming.html"),
    ("Black Panther", "https://altadefinizione.taipei/azione/9101-black-panther-streaming.html"),
    ("Thor: Ragnarok", "https://altadefinizione.taipei/avventura/1213-thor-ragnarok-streaming.html"),
    ("Spider-Man: Homecoming", "https://altadefinizione.taipei/azione/1415-spider-man-homecoming-streaming.html"),
    ("Doctor Strange", "https://altadefinizione.taipei/fantascienza/1617-doctor-strange-streaming.html"),
    ("Guardians of the Galaxy", "https://altadefinizione.taipei/fantascienza/1819-guardians-of-the-galaxy-streaming.html"),
    ("Avengers: Endgame", "https://altadefinizione.taipei/azione/2021-avengers-endgame-streaming.html"),
    ("Thunderbolts", "https://altadefinizione.taipei/avventura/24436-thunderbolts-streaming-gratis.html")
]

# Configura il browser headless
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Usa new headless se supportato
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=chrome_options)
m3u8_links = []

print("Elaborazione dei seguenti 10 titoli Marvel:\n")

for idx, (title, url) in enumerate(marvel_links, 1):
    print(f"{idx}. Titolo: {title} ({url})")
    try:
        driver.get(url)
        time.sleep(5)

        # Switcha all’iframe se presente
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            driver.switch_to.frame(iframes[0])
            time.sleep(3)

        # Trova eventuali link m3u8 nelle sorgenti della pagina
        sources = driver.page_source
        if ".m3u8" in sources:
            start = sources.find("https://")
            end = sources.find(".m3u8", start) + 5
            m3u8_url = sources[start:end]
            m3u8_links.append(f"#EXTINF:-1,{title}\n{m3u8_url}")
            print(f" - Trovato link M3U8: {m3u8_url}\n")
        else:
            print(f" - Nessun link M3U8 trovato.\n")
        
        driver.switch_to.default_content()

    except TimeoutException:
        print(f" - Timeout nell'elaborazione di {title}\n")
    except WebDriverException as e:
        print(f" - Errore WebDriver per {title}: {e}\n")

# Scrivi l'M3U8 finale
output_path = "films.m3u8"
with open(output_path, "w") as f:
    f.write("#EXTM3U\n")
    for line in m3u8_links:
        f.write(line + "\n")

print(f"File M3U8 salvato in: {output_path}")
driver.quit()
