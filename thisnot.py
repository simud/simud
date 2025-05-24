import cloudscraper
from bs4 import BeautifulSoup
import base64
import re
import logging
import time
import html
from urllib.parse import urljoin, unquote
import json

# Configura il logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='stream_processor.log',
    filemode='w'
)

# Associazioni (invariate)
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
    "Eurosport2_IT": "EuroSport 2",
    "SportMotoGP_IT": "Sky Sport MotoGP",
    "SportNBA_IT": "Sky Sport NBA",
    "Sport24_IT": "Sky Sport 24",
    "SportF1_IT": "Sky Sport F1",
    "TNTSP1": "TNT Sports 1",
    "Bundesliga1": "Sky Sport Bundesliga",
    "TSN5": "TSN 5"
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
    "EuroSport 2": "eurosport2.it",
    "Sky Sport MotoGP": "skysportmotogp.it",
    "Sky Sport NBA": "skysportnba.it",
    "Sky Sport 24": "skysport24.it",
    "Sky Sport F1": "skysportf1.it",
    "TNT Sports 1": "tntsports1.uk",
    "Sky Sport Bundesliga": "skysportbundesliga.de",
    "TSN 5": "tsn5.ca"
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
    "EuroSport 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/eurosport-2-es.png",
    "Sky Sport MotoGP": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-motogp-it.png",
    "Sky Sport NBA": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-nba-it.png",
    "Sky Sport 24": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-24-it.png",
    "Sky Sport F1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-f1-it.png",
    "TNT Sports 1": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/TNT_Sports_Logo_2023.svg/800px-TNT_Sports_Logo_2023.svg.png",
    "Sky Sport Bundesliga": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/germany/sky-sport-bundesliga-de.png",
    "TSN 5": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7d/TSN5_logo.svg/1200px-TSN5_logo.svg.png"
}

# Funzione per autenticarsi (invariata)
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

# Funzione per correggere il padding base64 (invariata)
def fix_base64_padding(encoded_keys):
    encoded_keys = encoded_keys.strip()
    padding_needed = (4 - (len(encoded_keys) % 4)) % 4
    encoded_keys += '=' * padding_needed
    return encoded_keys

# Funzione per decriptare il token (modificata per gestire chiavi multiple)
def decrypt_token(encoded_keys):
    try:
        encoded_keys = unquote(encoded_keys)
        print(f"[DEBUG] Stringa base64 dopo decodifica URL: {encoded_keys}")
        logging.debug(f"Stringa base64 dopo decodifica URL: {encoded_keys}")

        encoded_keys = fix_base64_padding(encoded_keys)
        print(f"[DEBUG] Stringa base64 dopo correzione padding: {encoded_keys}")
        logging.debug(f"Stringa base64 dopo correzione padding: {encoded_keys}")

        if len(encoded_keys) % 4 != 0:
            print(f"[ERRORE] Lunghezza stringa base64 non valida: {len(encoded_keys)}")
            logging.error(f"Lunghezza stringa base64 non valida: {len(encoded_keys)}")
            return []

        decoded = base64.b64decode(encoded_keys).decode('utf-8')

        try:
            json_data = json.loads(decoded)
            if isinstance(json_data, dict):
                keys = [(key_id, key) for key_id, key in json_data.items()]
                print(f"[SUCCESSO] Token JSON decodificato: {keys}")
                logging.debug(f"Token JSON decodificato: {keys}")
                return keys
        except json.JSONDecodeError:
            if ':' in decoded:
                key_pairs = decoded.split(',')
                keys = []
                for pair in key_pairs:
                    if ':' in pair:
                        key_id, key = pair.split(':', 1)
                        keys.append((key_id, key))
                        print(f"[SUCCESSO] Token standard decodificato: key_id={key_id}, key={key}")
                        logging.debug(f"Token standard decodificato: key_id={key_id}, key={key}")
                return keys
            else:
                print(f"[AVVISO] La stringa decodificata non contiene il separatore ':' né è un JSON valido: {decoded}")
                logging.warning(f"La stringa decodificata non contiene il separatore ':' né è un JSON valido: {decoded}")
                return []
    except Exception as e:
        print(f"[ERRORE] Errore nella decodifica del token: {e}")
        logging.error(f"Errore nella decodifica del token: {e}")
        return []

# Funzione modificata per estrarre il flusso MPD/M3U8 e le chiavi
def get_stream_and_key(scraper, url, channel_name):
    print(f"[INFO] Accesso al codice sorgente: {url}")
    try:
        response = scraper.get(url, timeout=5, allow_redirects=True)
        response.raise_for_status()
        print(f"[SUCCESSO] URL finale dopo reindirizzamenti: {response.url}")
        logging.debug(f"URL finale dopo reindirizzamenti: {response.url}")
        page_source = response.text

        debug_id = url.split('id=')[-1] if 'id=' in url else channel_name.replace(' ', '_')
        with open(f"debug_source_{debug_id}.html", 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"[DEBUG] Codice sorgente salvato in debug_source_{debug_id}.html")

        stream_pattern = re.compile(
            r'(?:(?:chrome-extension://[^\s]+?/pages/player\.html#)?)(https?://.+?\.(?:mpd|m3u8))(?:\?(?:[^&]*&)*ck=([^\s"]+))?(?="|\'|\s|$)',
            re.IGNORECASE
        )
        stream_matches = stream_pattern.findall(page_source)

        if not stream_matches:
            print(f"[AVVISO] Nessun flusso MPD/M3U8 trovato in {url}")
            logging.warning(f"Nessun flusso MPD/M3U8 trovato in {url}")
            return []

        results = []
        for stream_url, encoded_keys in stream_matches:
            stream_url = html.unescape(stream_url)
            print(f"[SUCCESSO] Flusso trovato: {stream_url}")
            print(f"[DEBUG] Flusso {stream_url} associato al canale: {channel_name}")
            logging.debug(f"Flusso trovato: {stream_url}, associato al canale: {channel_name}")

            if encoded_keys:
                key_list = encoded_keys.split(',')
                for idx, key in enumerate(key_list, 1):
                    keys = decrypt_token(key)
                    if keys:
                        for key_id, key_value in keys:
                            results.append((stream_url, key_id, key_value, idx))
                            print(f"[INFO] Aggiunta chiave {idx}: {key_id}:{key_value}")
                            logging.debug(f"Aggiunta chiave {idx}: {key_id}:{key_value}")
                    else:
                        print(f"[AVVISO] Chiave non valida: {key}, salto questa chiave")
                        logging.warning(f"Chiave non valida: {key}, salto questa chiave")
            else:
                results.append((stream_url, None, None, 1))
                print(f"[AVVISO] Nessun parametro ck= trovato per {stream_url}")
                logging.warning(f"Nessun parametro ck= trovato per {stream_url}")

        return results

    except Exception as e:
        print(f"[ERRORE] Errore nel processamento di {url}: {e}")
        logging.error(f"Errore nel processamento di {url}: {e}")
        return []

# Funzione per ottenere le informazioni del canale (invariata)
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

# Funzione modificata per creare una voce M3U
def create_m3u_entry(channel_name, url_id, stream_url, key_id, key, group_title, key_index):
    info = get_channel_info(url_id, group_title)
    group_title_upper = info["group_title"].upper()

    # Aggiungi un suffisso per distinguere i canali clonati
    clone_suffix = f" (Key {key_index})" if key_index > 1 else ""
    extinf = f'#EXTINF:-1 tvg-id="{info["tvg_id"]}" tvg-logo="{info["tvg_logo"]}" group-title="{group_title_upper}",{channel_name} {info["suffix"]}{clone_suffix}'
    if key_id and key:
        kodiprop_license_type = '#KODIPROP:inputstream.adaptive.license_type=clearkey'
        kodiprop_license_key = f'#KODIPROP:inputstream.adaptive.license_key={key_id}:{key}'
        return f"{extinf}\n{kodiprop_license_type}\n{kodiprop_license_key}\n{stream_url}\n"
    return f"{extinf}\n{stream_url}\n"

# Funzione principale modificata
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

    main_cards = soup.find_all('div', class_='card text-white mb-5')
    if not main_cards:
        print("[AVVISO] Nessun contenitore principale trovato nella pagina!")
        logging.warning("Nessun contenitore principale trovato nella pagina!")
        return

    print(f"[SUCCESSO] Trovati {len(main_cards)} contenitori principali")
    logging.info(f"Trovati {len(main_cards)} contenitori principali")
    channels = []

    with open("debug_links.txt", 'w', encoding='utf-8') as f:
        f.write("Link trovati nella pagina eventi:\n")

    for idx, main_card in enumerate(main_cards):
        header = main_card.find('div', class_='card-header')
        group_title = header.text.strip() if header else f"Sport_{idx}"
        print(f"[INFO] Elaborazione categoria: {group_title}")

        with open(f"debug_main_card_{idx}.html", 'w', encoding='utf-8') as f:
            f.write(str(main_card))
        print(f"[DEBUG] Contenitore principale salvato in debug_main_card_{idx}.html")

        links = main_card.find_all('a', href=re.compile(r'player\.php\?id=\w+'))
        print(f"[DEBUG] Trovati {len(links)} link ai player per la categoria {group_title}")
        logging.debug(f"Trovati {len(links)} link ai player per la categoria {group_title}")

        if not links:
            print(f"[AVVISO] Nessun link ai player trovato per la categoria: {group_title}")
            logging.warning(f"Nessun link ai player trovato per la categoria: {group_title}")
            continue

        with open("debug_links.txt", 'a', encoding='utf-8') as f:
            f.write(f"\nCategoria: {group_title}\n")
            for link in links:
                f.write(f"{link['href']}\n")

        for link in links:
            stream_url = urljoin(url, link['href'])
            url_id = stream_url.split('id=')[-1] if 'id=' in stream_url else group_title.replace(' ', '_')

            prev_b = link.find_previous('b')
            if prev_b and prev_b.text.strip() and not prev_b.get('class', ['']).count('date') and not prev_b.get('class', ['']).count('title'):
                channel_name = prev_b.text.strip()
            else:
                channel_name = url_id
                print(f"[AVVISO] Nome canale non trovato per {stream_url}, usato url_id: {channel_name}")
                logging.warning(f"Nome canale non trovato per {stream_url}, usato url_id: {channel_name}")

            print(f"[INFO] Elaborazione link: {stream_url}, Nome canale: {channel_name}, Group-title: {group_title}")
            logging.debug(f"Elaborazione link: {stream_url}, Nome canale: {channel_name}, Group-title: {group_title}")

            stream_results = get_stream_and_key(scraper, stream_url, channel_name)
            if stream_results:
                for stream, key_id, key, key_index in stream_results:
                    entry = create_m3u_entry(channel_name, url_id, stream, key_id, key, group_title, key_index)
                    channels.append(entry)
                    print(f"[SUCCESSO] Canale aggiunto: {channel_name} (Key {key_index}), Flusso: {stream}, Group-title: {group_title}")
                    logging.debug(f"Canale aggiunto: {channel_name} (Key {key_index}), Flusso: {stream}, Group-title: {group_title}")
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
