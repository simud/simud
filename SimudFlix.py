import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin, urlparse, quote
from collections import defaultdict
import time
import logging

# Configura il logging
logging.basicConfig(filename='m3u8.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configura il file M3U8
output_path = os.path.join("films.m3u8")  # Percorso relativo per GitHub
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
base_url = "https://altadefinizione.taipei/"
providers = ['supervideo', 'dropload', 'mixdrop', 'doodstream']

# Mappa per formattare i nomi dei provider
provider_names = {
    'supervideo': 'SuperVideo',
    'dropload': 'Dropload',
    'mixdrop': 'MixDrop',
    'doodstream': 'DoodStream'
}

# Lista completa dei film MCU
mcu_films = [
    "Iron Man",
    "The Incredible Hulk",
    "Iron Man 2",
    "Thor",
    "Captain America: The First Avenger",
    "The Avengers",
    "Iron Man 3",
    "Thor: The Dark World",
    "Captain America: The Winter Soldier",
    "Guardians of the Galaxy",
    "Avengers: Age of Ultron",
    "Ant-Man",
    "Captain America: Civil War",
    "Doctor Strange",
    "Guardians of the Galaxy Vol. 2",
    "Spider-Man: Homecoming",
    "Thor: Ragnarok",
    "Black Panther",
    "Avengers: Infinity War",
    "Ant-Man and the Wasp",
    "Captain Marvel",
    "Avengers: Endgame",
    "Spider-Man: Far From Home",
    "Black Widow",
    "Shang-Chi and the Legend of the Ten Rings",
    "Eternals",
    "Spider-Man: No Way Home",
    "Doctor Strange in the Multiverse of Madness",
    "Thor: Love and Thunder",
    "Black Panther: Wakanda Forever",
    "Ant-Man and the Wasp: Quantumania",
    "Guardians of the Galaxy Vol. 3",
    "The Marvels",
    "Deadpool & Wolverine",
    "Captain America: Brave New World",
    "Thunderbolts",
    "The Fantastic Four: First Steps"
]

# URL noti come fallback
known_urls = {
    "Iron Man": "https://altadefinizione.taipei/azione/1752-iron-man-1-streaming.html",
    "Thunderbolts": "https://altadefinizione.taipei/avventura/24436-thunderbolts-streaming-gratis.html"
}

# Intestazioni per le richieste HTTP
headers = {
    'User-Agent': user_agent,
    'Referer': base_url,
    'Origin': base_url
}

# Funzione per estrarre il dominio dall'URL
def get_domain(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"

# Funzione per generare uno slug dal titolo
def generate_slug(title):
    slug = title.lower().replace(':', '').replace(' & ', '-and-').replace(' ', '-')
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    return slug

# Funzione per generare un URL ipotetico
def generate_hypothetical_url(title, category='azione', id_guess=1752):
    slug = generate_slug(title)
    return f"{base_url}{category}/{id_guess}-{slug}-streaming.html"

# Funzione per verificare la validità di un URL
def is_valid_url(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return True
            return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Errore nella verifica di {url}, tentativo {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff esponenziale
    return False

# Funzione per cercare un titolo tramite Search1API
def search_with_search1api(title, max_retries=3):
    api_url = "https://api.search1api.com/search"
    data = {
        "query": f"site:altadefinizione.taipei {title}",
        "search_service": "google",
        "max_results": 5,
        "language": "it"
    }
    headers_api = {
        "Content-Type": "application/json"
    }
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, headers=headers_api, json=data, timeout=10)
            response.raise_for_status()
            results = response.json()
            for result in results.get('results', []):
                url = result.get('url', '')
                if 'altadefinizione.taipei' in url and re.match(r'.*/[a-zA-Z0-9-]+/[0-9]+-[a-zA-Z0-9-]+\.html', url):
                    logging.info(f"Trovato URL per {title} tramite Search1API: {url}")
                    return url
            logging.warning(f"Nessun risultato valido trovato per {title} tramite Search1API")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Errore nella ricerca con Search1API per {title}, tentativo {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            return None

# Funzione per trovare l'URL di un titolo
def find_film_url(title):
    # 1. Controlla gli URL noti
    if title in known_urls:
        url = known_urls[title]
        if is_valid_url(url):
            return url
        logging.warning(f"URL noto non valido per {title}: {url}")

    # 2. Prova con Search1API
    api_url = search_with_search1api(title)
    if api_url and is_valid_url(api_url):
        return api_url

    # 3. Genera e verifica URL ipotetici
    categories = ['azione', 'avventura', 'fantascienza']
    for category in categories:
        for id_guess in range(1752, 1755):  # Prova alcuni ID vicini a quelli noti
            url = generate_hypothetical_url(title, category, id_guess)
            if is_valid_url(url):
                logging.info(f"Trovato URL ipotetico valido per {title}: {url}")
                return url
    logging.warning(f"Nessun URL trovato per {title}")
    return None

# Inizializza il file M3U8
with open(output_path, 'w', encoding='utf-8') as m3u8_file:
    m3u8_file.write('#EXTM3U\n')

valid_titles_count = 0
processed_urls = set()

try:
    print("Elaborazione dei film MCU:")
    for i, title in enumerate(mcu_films, 1):
        print(f"\n{i}. Ricerca per: {title}")
        logging.info(f"Inizio ricerca per: {title}")

        # Trova l'URL del film
        base_href = find_film_url(title)
        if not base_href:
            print(f" - Nessun URL trovato per {title}")
            continue

        if base_href in processed_urls:
            print(f" - URL già elaborato per {title}: {base_href}")
            logging.info(f"URL già elaborato per {title}: {base_href}")
            continue
        processed_urls.add(base_href)

        # Cerca il link di mostraguarda.stream
        try:
            film_response = requests.get(base_href, headers=headers, timeout=10)
            film_response.raise_for_status()
            film_soup = BeautifulSoup(film_response.text, 'html.parser')

            # Cerca l'iframe con mostraguarda.stream
            mostraguarda_link = None
            iframe = film_soup.find('iframe', src=re.compile(r'https?://mostraguarda\.stream', re.IGNORECASE))
            if iframe:
                mostraguarda_link = iframe.get('src')
            else:
                # Cerca nei tag <script> come fallback
                for script in film_soup.find_all('script'):
                    if script.string:
                        match = re.search(r'(https?://mostraguarda\.stream/[^\s"\']+)', script.string, re.IGNORECASE)
                        if match:
                            mostraguarda_link = match.group(1)
                            break

            if not mostraguarda_link:
                print(f" - Nessun link mostraguarda.stream trovato per {title} ({base_href})")
                logging.warning(f"Nessun link mostraguarda.stream trovato per {title} ({base_href})")
                continue

            # Accedi al codice sorgente di mostraguarda.stream
            mostraguarda_response = requests.get(mostraguarda_link, headers=headers, timeout=10)
            mostraguarda_response.raise_for_status()
            mostraguarda_soup = BeautifulSoup(mostraguarda_response.text, 'html.parser')

            # Cerca gli embed in <ul class="_player-mirrors">
            embed_links = []
            player_mirrors = mostraguarda_soup.find('ul', class_='_player-mirrors')
            if player_mirrors:
                for li in player_mirrors.find_all('li'):
                    data_link = li.get('data-link')
                    if data_link and any(provider in data_link.lower() for provider in providers):
                        provider_name = next((p for p in providers if p in data_link.lower()), 'Provider')
                        if data_link.startswith('//'):
                            data_link = f"https:{data_link}"
                        embed_links.append({'href': data_link, 'text': provider_name})

            # Se non ci sono embed validi, salta il titolo
            if not embed_links:
                print(f" - Nessun embed valido trovato per {title} ({base_href}) in mostraguarda.stream")
                logging.warning(f"Nessun embed valido trovato per {title} ({base_href})")
                continue

            # Raggruppa gli embed per provider
            embeds_by_provider = defaultdict(list)
            for link in embed_links:
                embeds_by_provider[link['text']].append(link['href'])

            # Rimuovi duplicati
            embed_links = []
            for provider, urls in embeds_by_provider.items():
                for j, url in enumerate(urls, 1):
                    embed_links.append({'href': url, 'text': provider})

            # Stampa e salva i link di embed
            valid_titles_count += 1
            print(f"{valid_titles_count}. Titolo: {title}, URL: {base_href}")
            logging.info(f"Titolo: {title}, URL: {base_href}")
            with open(output_path, 'a', encoding='utf-8') as m3u8_file:
                for link in embed_links:
                    embed_url = link['href']
                    provider = link['text']
                    group_title = provider_names.get(provider, provider.capitalize())
                    embed_domain = get_domain(embed_url)
                    if len(embeds_by_provider[provider]) > 1:
                        episode_label = f"{1}.{embeds_by_provider[provider].index(embed_url) + 1:02d}"
                        m3u8_title = f"{title} {episode_label}"
                    else:
                        m3u8_title = title
                    print(f" - Embed ({provider}): {embed_url} [group-title={group_title}, origin={embed_domain}, referrer={embed_domain}]")
                    logging.info(f"Embed ({provider}): {embed_url} [group-title={group_title}, origin={embed_domain}, referrer={embed_domain}]")
                    m3u8_file.write(f'#EXTINF:-1 tvg-name="{m3u8_title}" group-title="{group_title}",{m3u8_title}\n')
                    m3u8_file.write(f'#EXTVLCOPT:http-origin={embed_domain}\n')
                    m3u8_file.write(f'#EXTVLCOPT:http-referrer={embed_domain}\n')
                    m3u8_file.write(f'#EXTVLCOPT:http-user-agent={user_agent}\n')
                    m3u8_file.write(f'{embed_url}\n')

        except Exception as e:
            print(f" - Errore nell'elaborazione di {title} ({base_href}): {e}")
            logging.error(f"Errore nell'elaborazione di {title} ({base_href}): {e}")

except Exception as e:
    print(f"Errore generale: {e}")
    logging.error(f"Errore generale: {e}")

finally:
    print(f"\nFile M3U8 salvato in: {output_path}")
    logging.info(f"File M3U8 salvato in: {output_path}")
