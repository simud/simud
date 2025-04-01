import requests
import re
import os
from bs4 import BeautifulSoup

base_url = "https://skystreaming.onl/"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://skystreaming.onl",
    "Referer": "https://skystreaming.onl/"
}

def find_event_pages():
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        event_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.match(r'/view/[^/]+/[^/]+', href):
                full_url = base_url + href.lstrip('/')
                event_links.add(full_url)
            elif re.match(r'https://skystreaming\.onl/view/[^/]+/[^/]+', href):
                event_links.add(href)

        return list(event_links)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine evento: {e}")
        return []

if __name__ == "__main__":
    event_pages = find_event_pages()
    print(event_pages)
