import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin, urlparse, quote
from collections import defaultdict

# Salva il file nella directory del progetto
output_path = os.path.join(os.path.dirname(__file__), "films.m3u8")

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
url = "https://altadefinizione.taipei/"
providers = ['supervideo', 'dropload', 'mixdrop', 'doodstream']

provider_names = {
    'supervideo': 'SuperVideo',
    'dropload': 'Dropload',
    'mixdrop': 'MixDrop',
    'doodstream': 'DoodStream'
}

marvel_titles = [
    {"title": "Iron Man", "url": "https://altadefinizione.taipei/azione/1752-iron-man-1-streaming.html"},
    {"title": "The Avengers", "url": "https://altadefinizione.taipei/azione/1234-the-avengers-streaming.html"},
    {"title": "Captain America: Civil War", "url": "https://altadefinizione.taipei/azione/5678-captain-america-civil-war-streaming.html"},
    {"title": "Black Panther", "url": "https://altadefinizione.taipei/azione/9101-black-panther-streaming.html"},
    {"title": "Thor: Ragnarok", "url": "https://altadefinizione.taipei/avventura/1213-thor-ragnarok-streaming.html"},
    {"title": "Spider-Man: Homecoming", "url": "https://altadefinizione.taipei/azione/1415-spider-man-homecoming-streaming.html"},
    {"title": "Doctor Strange", "url": "https://altadefinizione.taipei/fantascienza/1617-doctor-strange-streaming.html"},
    {"title": "Guardians of the Galaxy", "url": "https://altadefinizione.taipei/fantascienza/1819-guardians-of-the-galaxy-streaming.html"},
    {"title": "Avengers: Endgame", "url": "https://altadefinizione.taipei/azione/2021-avengers-endgame-streaming.html"},
    {"title": "Thunderbolts", "url": "https://altadefinizione.taipei/avventura/24436-thunderbolts-streaming-gratis.html"}
]

headers = {
    'User-Agent': user_agent,
    'Referer': url,
    'Origin': url
}

def get_domain(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"

def search_title(title):
    search_url = f"{url}?s={quote(title)}"
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        film_elements = soup.find_all('a', href=re.compile(r'/[a-zA-Z0-9-]+/[0-9]+-[a-zA-Z0-9-]+\.html'))
        for element in film_elements:
            title_element = element.find(['h2', 'h3', 'span', 'div'], class_=re.compile(r'title|movie-title|film-title', re.IGNORECASE))
            if title_element and title.lower() in title_element.get_text(strip=True).lower():
                film_url = element.get('href')
                if film_url.startswith('/'):
                    film_url = urljoin(url, film_url)
                return film_url
        return None
    except Exception as e:
        print(f" - Errore nella ricerca di {title}: {e}")
        return None

# Inizializza il file M3U8
with open(output_path, 'w', encoding='utf-8') as m3u8_file:
    m3u8_file.write('#EXTM3U\n')

valid_titles_count = 0
max_titles = 10
processed_urls = set()

try:
    print("Elaborazione dei seguenti 10 titoli Marvel:")
    for i, item in enumerate(marvel_titles, 1):
        if valid_titles_count >= max_titles:
            break

        title = item['title']
        base_href = item['url']
        print(f"\n{i}. Titolo: {title} ({base_href})")

        if base_href in processed_urls:
            print(f" - URL già elaborato per {title}")
            continue

        try:
            film_response = requests.get(base_href, headers=headers, timeout=10)
            film_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f" - Errore con l'URL diretto per {title} ({base_href}): {e}")
            base_href = search_title(title)
            if not base_href:
                print(f" - Nessun risultato trovato per {title} tramite ricerca")
                continue
            print(f" - Trovato URL alternativo per {title}: {base_href}")

        processed_urls.add(base_href)

        try:
            film_response = requests.get(base_href, headers=headers, timeout=10)
            film_response.raise_for_status()
            film_soup = BeautifulSoup(film_response.text, 'html.parser')

            mostraguarda_link = None
            iframe = film_soup.find('iframe', src=re.compile(r'https?://mostraguarda\.stream', re.IGNORECASE))
            if iframe:
                mostraguarda_link = iframe.get('src')
            else:
                for script in film_soup.find_all('script'):
                    if script.string:
                        match = re.search(r'(https?://mostraguarda\.stream/[^\s"\']+)', script.string, re.IGNORECASE)
                        if match:
                            mostraguarda_link = match.group(1)
                            break

            if not mostraguarda_link:
                print(f" - Nessun link mostraguarda.stream trovato per {title} ({base_href})")
                continue

            mostraguarda_response = requests.get(mostraguarda_link, headers=headers, timeout=10)
            mostraguarda_response.raise_for_status()
            mostraguarda_soup = BeautifulSoup(mostraguarda_response.text, 'html.parser')

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

            if not embed_links:
                print(f" - Nessun embed valido trovato per {title} ({base_href}) in mostraguarda.stream, titolo saltato")
                continue

            embeds_by_provider = defaultdict(list)
            for link in embed_links:
                embeds_by_provider[link['text']].append(link['href'])

            embed_links = []
            for provider, urls in embeds_by_provider.items():
                for j, url in enumerate(urls, 1):
                    embed_links.append({'href': url, 'text': provider})

            valid_titles_count += 1
            print(f"{valid_titles_count}. Titolo: {title}, URL: {base_href}")
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
                    m3u8_file.write(f'#EXTINF:-1 tvg-name="{m3u8_title}" group-title="{group_title}",{m3u8_title}\n')
                    m3u8_file.write(f'#EXTVLCOPT:http-origin={embed_domain}\n')
                    m3u8_file.write(f'#EXTVLCOPT:http-referrer={embed_domain}\n')
                    m3u8_file.write(f'#EXTVLCOPT:http-user-agent={user_agent}\n')
                    m3u8_file.write(f'{embed_url}\n')

        except Exception as e:
            print(f" - Errore nell'elaborazione di {title} ({base_href}): {e}")

except Exception as e:
    print(f"Errore generale: {e}")

finally:
    print(f"\nFile M3U8 salvato in: {output_path}")
