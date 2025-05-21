import cloudscraper
from bs4 import BeautifulSoup
import base64
import re
import logging
import time
import html
from urllib.parse import urljoin

# Configura il logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='stream_processor.log',
    filemode='w'
)

# Associazioni
channel_associations = {
    "SportCalcio_IT": "Sky Sport Calcio",
    "SportUno_IT": "Sky Sport UNO",
    "USA": "USA Network",
    "Sport251_IT": "Sky Sport 251",
    "DaznB1": "DAZN 1",
    "DaznB2": "DAZN 2",
    "Sport252_IT": "Sky Sport 252",
    "Sport253_IT": "Sky Sport 253",
    "Sport254_IT": "Sky Sport 254",
    "Sport255_IT": "Sky Sport 255",
    "Eurosport1_IT": "EuroSport 1",
    "SportMotoGP_IT": "Sky Sport MotoGP",
    "SportNBA_IT": "Sky Sport NBA"
}

tvg_id_associations = {
    "Sky Sport Calcio": "skysportcalcio.it",
    "Sky Sport UNO": "skysportuno.it",
    "USA Network": "usa.it",
    "Sky Sport 251": "skysport251.it",
    "DAZN 1": "dazn1.it",
    "DAZN 2": "dazn2.it",
    "Sky Sport 252": "skysport252.it",
    "Sky Sport 253": "skysport253.it",
    "Sky Sport 254": "skysport254.it",
    "Sky Sport 255": "skysport255.it",
    "EuroSport 1": "eurosport1.it",
    "Sky Sport MotoGP": "skysportmotogp.it",
    "Sky Sport NBA": "skysportnba.it"
}

logo_associations = {
    "Sky Sport Calcio": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-calcio-it.png",
    "Sky Sport UNO": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-uno-it.png",
    "USA Network": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/usa/usa-network-us.png",
    "Sky Sport 251": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-251-it.png",
    "DAZN 1": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/DAZN_1_Logo.svg/774px-DAZN_1_Logo.svg.png",
    "DAZN 2": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/DAZN_1_Logo.svg/774px-DAZN_1_Logo.svg.png",
    "Sky Sport 252": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-252-it.png",
    "Sky Sport 253": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-253-it.png",
    "Sky Sport 254": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-254-it.png",
    "Sky Sport 255": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-255-it.png",
    "EuroSport 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/eurosport-1-es.png",
    "Sky Sport MotoGP": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-motogp-it.png",
    "Sky Sport NBA": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-nba-it.png"
}

# Funzione per autenticarsi
def authenticate(scraper, login_url, password):
    print(f"[INFO] Tentativo di autenticazione su {login_url}")
    try:
        payload = {'password': password}
        response = scraper.post(login_url, data=payload, timeout=5, allow_redirects=True)
        response.raise_for_status()
        print(f"[SUCCESSO] Autenticazione completata. URL finale: {response.url}")
        logging.debug(f"Autenticazione completata. URL finale: {response.url}")
        return response
    except Exception as e:
        print(f"[ERRORE] Autenticazione fallita: {e}")
        logging.error(f"Errore durante l'autenticazione: {e}")
        return None

# Funzione per decriptare il token (placeholder)
def decrypt_token(encoded_keys):
    try:
        decoded = base64.b64decode(encoded_keys).decode('utf-8')
        if ':' in decoded:
            key_id, key = decoded.split(':', 1)
            print(f"[SUCCESSO] Token decodificato: key_id={key_id}, key={key}")
            logging.debug(f"Token decodificato: key_id={key_id}, key={key}")
            return key_id, key
        else:
            print(f"[AVVISO] La stringa decodificata non contiene il separatore ':'")
            logging.warning("La stringa decodificata non contiene il separatore ':'")
            return None, None
    except Exception as e:
        print(f"[ERRORE] Errore nella decodifica del token: {e}")
        logging.error(f"Errore nella decodifica del token: {e}")
        return None, None

# Funzione per estrarre il flusso MPD/M3U8 e la chiave
def get_stream_and_key(scraper, url, channel_name):
    print(f"[INFO] Accesso al codice sorgente: {url}")
    try:
        response = scraper.get(url, timeout=5, allow_redirects=True)
        response.raise_for_status()
        print(f"[SUCCESSO] URL finale dopo reindirizzamenti: {response.url}")
        logging.debug(f"URL finale dopo reindirizzamenti: {response.url}")
        page_source = response.text

        # Salva il codice sorgente per debug
        debug_id = url.split('id=')[-1] if 'id=' in url else channel_name.replace(' ', '_')
        with open(f"debug_source_{debug_id}.html", 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"[DEBUG] Codice sorgente salvato in debug_source_{debug_id}.html")

        # Cerca flussi MPD/M3U8
        stream_pattern = re.compile(
            r'(?:chrome-extension://[^\s]+?)?(?:player\.html#)?(https?://.+?\.(?:mpd|m3u8))(?:[?&]ck=([^\s&]+))?(?="|\'|\s|$)',
            re.IGNORECASE
        )
        stream_matches = stream_pattern.findall(page_source)

        if not stream_matches:
            print(f"[AVVISO] Nessun flusso MPD/M3U8 trovato in {url}")
            logging.warning(f"Nessun flusso MPD/M3U8 trovato in {url}")
            return None, None, None

        # Prendi il primo flusso valido
        stream_url, encoded_keys = stream_matches[0]
        stream_url = html.unescape(stream_url)
        print(f"[SUCCESSO] Flusso trovato: {stream_url}")
        print(f"[DEBUG] Flusso {stream_url} associato al canale: {channel_name}")
        logging.debug(f"Flusso trovato: {stream_url}, associato al canale: {channel_name}")

        # Gestione del token
        if encoded_keys:
            key_id, key = decrypt_token(encoded_keys)
            return stream_url, key_id, key
        else:
            print(f"[AVVISO] Nessun parametro ck= trovato in {url}")
            logging.warning(f"Nessun parametro ck= trovato in {url}")
            return stream_url, None, None

    except Exception as e:
        print(f"[ERRORE] Errore nel processamento di {url}: {e}")
        logging.error(f"Errore nel processamento di {url}: {e}")
        return None, None, None

# Funzione per ottenere le informazioni del canale
def get_channel_info(url_id, group_title):
    tvg_name = channel_associations.get(url_id, url_id)
    tvg_id = tvg_id_associations.get(tvg_name, "")
    logo = logo_associations.get(tvg_name, "")
    suffix = "(HD)" if "hd" in url_id.lower() else ""

    return {
        "tvg_id": tvg_id,
        "tvg_name": tvg_name,
        "tvg_logo": logo,
        "group_title": group_title,
        "suffix": suffix
    }

# Funzione per creare una voce M3U
def create_m3u_entry(channel_name, url_id, stream_url, key_id, key, group_title):
    info = get_channel_info(url_id, group_title)

    extinf = f'#EXTINF:-1 tvg-id="{info["tvg_id"]}" tvg-logo="{info["tvg_logo"]}" group-title="{info["group_title"]}",{channel_name} {info["suffix"]}'
    if key_id and key:
        kodiprop_license_type = '#KODIPROP:inputstream.adaptive.license_type=clearkey'
        kodiprop_license_key = f'#KODIPROP:inputstream.adaptive.license_key={key_id}:{key}'
        return f"{extinf}\n{kodiprop_license_type}\n{kodiprop_license_key}\n{stream_url}\n"
    return f"{extinf}\n{stream_url}\n"

# Funzione principale
def create_m3u8_list():
    url = "https://thisnot.business/eventi.php"
    login_url = "https://thisnot.business/index.php"
    password = "2025"

    print(f"[INFO] Inizio elaborazione. URL eventi: {url}")
    scraper = cloudscraper.create_scraper()

    auth_response = authenticate(scraper, login_url, password)
    if not auth_response:
        print("[ERRORE] Autenticazione fallita. Impossibile proseguire.")
        logging.error("Autenticazione fallita. Impossibile proseguire.")
        return

    print(f"[INFO] Accesso alla pagina eventi: {url}")
    try:
        response = scraper.get(url, timeout=5, allow_redirects=True)
        response.raise_for_status()
        print(f"[SUCCESSO] URL finale dopo reindirizzamenti: {response.url}")
        logging.debug(f"URL finale dopo reindirizzamenti: {response.url}")
        soup = BeautifulSoup(response.text, 'html.parser')

        with open("debug_eventi.html", 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("[DEBUG] Codice sorgente della pagina eventi salvato in debug_eventi.html")
    except Exception as e:
        print(f"[ERRORE] Errore nell'accesso a {url}: {e}")
        logging.error(f"Errore nell'accesso a {url}: {e}")
        return

    # Trova tutti i link nella pagina
    links = soup.find_all('a', href=re.compile(r'player\.php\?id=\w+'))
    if not links:
        print("[AVVISO] Nessun link ai player trovato nella pagina!")
        logging.warning("Nessun link ai player trovato nella pagina!")
        logging.debug(f"Contenuto pagina (primi 4000 caratteri): {response.text[:4000]}")
        return

    print(f"[SUCCESSO] Trovati {len(links)} link ai player")
    logging.info(f"Trovati {len(links)} link ai player")
    channels = []

    with open("debug_links.txt", 'w', encoding='utf-8') as f:
        f.write("Link trovati nella pagina eventi:\n")

    for idx, link in enumerate(links):
        stream_url = urljoin(url, link['href'])
        url_id = stream_url.split('id=')[-1] if 'id=' in stream_url else f"unknown_{idx}"

        # Cerca il tag <b> immediatamente precedente al link per il nome del canale
        channel_name = None
        prev_b = link.find_previous('b')
        if prev_b and prev_b.text.strip() and not prev_b.get('class', ['']).count('date') and not prev_b.get('class', ['']).count('title'):
            channel_name = prev_b.text.strip()
        else:
            # Fallback: usa l'url_id se non c'è un nome evento valido
            channel_name = url_id
            print(f"[AVVISO] Nome canale non trovato per {stream_url}, usato url_id: {channel_name}")
            logging.warning(f"Nome canale non trovato per {stream_url}, usato url_id: {channel_name}")

        # Cerca il group-title più vicino (tag <b class="title">)
        group_title = "Sport"
        parent = link.parent
        while parent and parent.name != 'html':
            title_elem = parent.find_previous('b', class_='title')
            if title_elem and title_elem.text.strip():
                group_title = title_elem.text.strip()
                break
            parent = parent.parent

        print(f"[INFO] Elaborazione link: {stream_url}, Nome canale: {channel_name}, Group-title: {group_title}")
        logging.debug(f"Elaborazione link: {stream_url}, Nome canale: {channel_name}, Group-title: {group_title}")

        # Salva il link per debug
        with open("debug_links.txt", 'a', encoding='utf-8') as f:
            f.write(f"Link {idx}: {stream_url}, Canale: {channel_name}, Gruppo: {group_title}\n")

        stream, key_id, key = get_stream_and_key(scraper, stream_url, channel_name)
        if stream:
            entry = create_m3u_entry(channel_name, url_id, stream, key_id, key, group_title)
            channels.append(entry)
            print(f"[SUCCESSO] Canale aggiunto: {channel_name}, Flusso: {stream}, Group-title: {group_title}")
            logging.debug(f"Canale aggiunto: {channel_name}, Flusso: {stream}, Group-title: {group_title}")
        else:
            print(f"[AVVISO] Nessun flusso valido trovato per il link: {stream_url}")
            logging.warning(f"Nessun flusso valido trovato per il link: {stream_url}")

        time.sleep(0.5)

    m3u_file = "thisnot.m3u8"
    with open(m3u_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for entry in channels:
            f.write(entry)

    print(f"[SUCCESSO] File M3U generato: {m3u_file}")
    logging.info(f"Lista M3U creata con successo: {m3u_file}")

    if not channels:
        print("[AVVISO] La lista M3U è vuota! Nessun canale valido trovato.")
        logging.warning("La lista M3U è vuota! Nessun canale valido trovato.")

if __name__ == "__main__":
    create_m3u8_list()
