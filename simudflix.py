import cloudscraper
from bs4 import BeautifulSoup
import urllib.parse
import time
import logging
import random
import json
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

movies = [
    "Iron Man",
    "Iron Man 2",
    "Iron Man 3",
    "The Avengers",
    "Captain America: The First Avenger",
    "Thor",
    "Guardians of the Galaxy",
    "Doctor Strange",
    "Black Panther",
    "Avengers: Endgame"
]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
]

headers = {
    "User-Agent": random.choice(user_agents),
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
    "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

m3u_entries = []
base_url = "https://streamingcommunity.spa"
MAX_RETRIES = 3
TIMEOUT = 60
REQUEST_DELAY = 3
cookies = {}

def get_movie_id(title, scraper):
    global cookies
    for attempt in range(MAX_RETRIES):
        try:
            headers["User-Agent"] = random.choice(user_agents)
            encoded_title = urllib.parse.quote(title)
            search_url = f"{base_url}/api/search?q={encoded_title}"
            logging.info(f"Ricerco: {search_url} (User-Agent: {headers['User-Agent']})")
            res = scraper.get(search_url, headers=headers, cookies=cookies, timeout=TIMEOUT)

            if res.status_code != 200:
                logging.error(f"Errore HTTP per '{title}': Stato {res.status_code}")
                time.sleep(REQUEST_DELAY)
                continue

            if "cf-browser-verification" in res.text or "Checking your browser" in res.text:
                logging.error(f"Pagina di verifica Cloudflare non bypassata per '{title}'")
                time.sleep(REQUEST_DELAY)
                continue

            cookies.update(res.cookies.get_dict())
            try:
                data = res.json()
                for result in data.get('data', []):
                    movie_id = result.get('id')
                    if movie_id and str(movie_id).isdigit():
                        return str(movie_id)
            except ValueError:
                soup = BeautifulSoup(res.text, "html.parser")
                result = soup.select_one("div.card a[href*='/watch/']") or soup.select_one("a[href*='/watch/']")
                if not result:
                    break
                href = result['href']
                movie_id = href.split('/')[-1]
                if movie_id.isdigit():
                    return movie_id
        except Exception as e:
            logging.error(f"Errore nella ricerca per '{title}': {e}")
            time.sleep(REQUEST_DELAY)
    return None

def get_m3u8_url(movie_id, title, scraper):
    global cookies
    for attempt in range(MAX_RETRIES):
        try:
            headers["User-Agent"] = random.choice(user_agents)
            video_url = f"{base_url}/api/video/{movie_id}"
            res = scraper.get(video_url, headers=headers, cookies=cookies, timeout=TIMEOUT)

            if res.status_code == 200 and "application/json" in res.headers.get("Content-Type", ""):
                try:
                    data = res.json()
                    m3u_url = data.get('url') or data.get('playlist') or data.get('m3u8')
                    if m3u_url and "vixcloud.co/playlist" in m3u_url:
                        return m3u_url
                except ValueError:
                    pass

            watch_url = f"{base_url}/watch/{movie_id}"
            res = scraper.get(watch_url, headers=headers, cookies=cookies, timeout=TIMEOUT)
            if res.status_code != 200:
                continue

            if "cf-browser-verification" in res.text:
                time.sleep(REQUEST_DELAY)
                continue

            cookies.update(res.cookies.get_dict())
            soup = BeautifulSoup(res.text, "html.parser")
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string and "vixcloud.co/playlist" in script.string:
                    match = re.search(r'(https://vixcloud\.co/playlist/\d+\?[^"\']+)', script.string)
                    if match:
                        return match.group(1)
            iframes = soup.find_all("iframe")
            for iframe in iframes:
                src = iframe.get('src', '')
                if "vixcloud.co/playlist" in src:
                    return src
        except Exception as e:
            logging.error(f"Errore nel recuperare M3U8 per '{title}': {e}")
            time.sleep(REQUEST_DELAY)
    return None

# FIX: rimossa opzione non supportata `sess`
scraper = cloudscraper.create_scraper(delay=30)

for title in movies:
    logging.info(f"Elaborazione: {title}")
    movie_id = get_movie_id(title, scraper)
    if movie_id:
        m3u_url = get_m3u8_url(movie_id, title, scraper)
        if m3u_url:
            m3u_entries.append(f"#EXTINF:-1,{title}\n{m3u_url}")
    time.sleep(REQUEST_DELAY)

if m3u_entries:
    with open("streaming.m3u8", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("\n".join(m3u_entries))
    logging.info("File streaming.m3u8 creato con successo.")
else:
    logging.warning("Nessun flusso M3U8 trovato. File non creato.")