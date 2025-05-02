# it/dogior/hadEnough/simudflix.py

import json
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Costanti
MAIN_URL = "https://streamingcommunity.spa"  # URL base del sito
NAME = "Streaming Community"
QUALITIES_UNKNOWN = 0  # Valore per qualità sconosciuta
M3U8_OUTPUT_FILE = "streaming.m3u8"  # Nome del file M3U8 generato

# Elenco delle categorie
CATEGORIES = {
    "Top 10 di oggi": f"{MAIN_URL}/browse/top10",
    "I Titoli Del Momento": f"{MAIN_URL}/browse/trending",
    "Aggiunti di Recente": f"{MAIN_URL}/browse/latest",
    "Animazione": f"{MAIN_URL}/browse/genre?g=Animazione",
    "Avventura": f"{MAIN_URL}/browse/genre?g=Avventura",
    "Azione": f"{MAIN_URL}/browse/genre?g=Azione",
    "Commedia": f"{MAIN_URL}/browse/genre?g=Commedia",
    "Crime": f"{MAIN_URL}/browse/genre?g=Crime",
    "Documentario": f"{MAIN_URL}/browse/genre?g=Documentario",
    "Dramma": f"{MAIN_URL}/browse/genre?g=Dramma",
    "Famiglia": f"{MAIN_URL}/browse/genre?g=Famiglia",
    "Fantascienza": f"{MAIN_URL}/browse/genre?g=Fantascienza",
    "Fantasy": f"{MAIN_URL}/browse/genre?g=Fantasy",
    "Horror": f"{MAIN_URL}/browse/genre?g=Horror",
    "Reality": f"{MAIN_URL}/browse/genre?g=Reality",
    "Romance": f"{MAIN_URL}/browse/genre?g=Romance",
    "Thriller": f"{MAIN_URL}/browse/genre?g=Thriller"
}

class StreamingCommunityExtractor:
    def __init__(self):
        self.main_url = MAIN_URL
        self.name = NAME
        self.requires_referer = False

    def get_all_categories(self, referer=None, output_file=M3U8_OUTPUT_FILE):
        """
        Estrae i flussi M3U8 da tutte le categorie e genera un file M3U8 combinato.

        :param referer: Referer della richiesta (opzionale)
        :param output_file: Nome del file M3U8 da generare
        :return: Contenuto del file M3U8 combinato o None in caso di errore
        """
        TAG = "GetAllCategories"
        logger.debug(f"{TAG} - Processing all categories")

        m3u8_contents = []
        for category_name, category_url in CATEGORIES.items():
            logger.info(f"{TAG} - Processing category: {category_name} ({category_url})")
            category_content = self.get_urls_from_category(category_url, referer=referer)
            if category_content:
                m3u8_contents.append(f"#EXTINF:-1,Category: {category_name}\n{category_content}")

        if not m3u8_contents:
            logger.error(f"{TAG} - Nessun flusso M3U8 estratto da nessuna categoria")
            return None

        # Combina i contenuti M3U8
        combined_m3u8 = "#EXTM3U\n" + "\n".join(m3u8_contents)
        
        # Salva il file M3U8
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(combined_m3u8)
        logger.info(f"{TAG} - File M3U8 combinato salvato come: {output_file}")

        return combined_m3u8

    def get_urls_from_category(self, category_url, referer=None, output_file=M3U8_OUTPUT_FILE):
        """
        Estrae i flussi M3U8 da una categoria e genera un file M3U8 combinato.

        :param category_url: URL della categoria (es. https://streamingcommunity.spa/browse/genre?g=Azione)
        :param referer: Referer della richiesta (opzionale)
        :param output_file: Nome del file M3U8 da generare
        :return: Contenuto del file M3U8 combinato o None in caso di errore
        """
        TAG = "GetUrlsFromCategory"
        logger.debug(f"{TAG} - CATEGORY URL: {category_url}")

        try:
            # Effettua la richiesta alla pagina della categoria
            response = requests.get(category_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Trova i link ai titoli (adatta il selettore in base all'HTML del sito)
            title_links = soup.select("a[href*='/watch/']")  # Processa tutti i titoli
            if not title_links:
                logger.error(f"{TAG} - Nessun titolo trovato nella categoria: {category_url}")
                return None

            m3u8_contents = []
            for link in title_links:
                title_url = f"{self.main_url}{link['href']}" if link['href'].startswith('/') else link['href']
                logger.debug(f"{TAG} - Processing title URL: {title_url}")
                m3u8_content = self.get_url(title_url, referer=referer)
                if m3u8_content:
                    title_name = link.get_text(strip=True) or "Titolo Sconosciuto"
                    m3u8_contents.append(f"#EXTINF:-1,{title_name}\n{m3u8_content}")

            if not m3u8_contents:
                logger.error(f"{TAG} - Nessun flusso M3U8 estratto dalla categoria: {category_url}")
                return None

            # Combina i contenuti M3U8 per la categoria
            combined_m3u8 = "\n".join(m3u8_contents)
            return combined_m3u8
        except requests.RequestException as e:
            logger.error(f"{TAG} - Errore durante la richiesta HTTP: {e}")
            return None
        except Exception as e:
            logger.error(f"{TAG} - Errore imprevisto: {e}")
            return None

    def get_url(self, url, referer=None, subtitle_callback=None, callback=None, output_file=M3U8_OUTPUT_FILE):
        """
        Estrae i link di streaming da un URL dato e genera un file M3U8.

        :param url: URL della pagina
        :param referer: Referer della richiesta (opzionale)
        :param subtitle_callback: Funzione di callback per i sottotitoli
        :param callback: Funzione di callback per i link estratti
        :param output_file: Nome del file M3U8 da generare (default: streaming.m3u8)
        :return: Contenuto del file M3U8 come stringa o None in caso di errore
        """
        TAG = "GetUrl"
        logger.debug(f"{TAG} - REFERER: {referer} URL: {url}")

        if not url:
            logger.error(f"{TAG} - Nessun URL fornito")
            return None

        try:
            # Effettua la richiesta alla pagina
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Solleva un'eccezione per codici di stato HTTP non validi
            soup = BeautifulSoup(response.text, 'html.parser')
            iframe = soup.select_one("iframe")
            if not iframe:
                logger.error(f"{TAG} - Nessun iframe trovato nella pagina: {url}")
                return None
            iframe_src = iframe["src"]
            playlist_url = self._get_playlist_link(iframe_src)
            if not playlist_url:
                logger.error(f"{TAG} - Impossibile ottenere l'URL della playlist")
                return None
            logger.warning(f"{TAG} - FINAL URL: {playlist_url}")

            # Crea il contenuto del file M3U8
            m3u8_content = self._generate_m3u8_content(playlist_url, referer)
            
            # Crea il link estratto per il callback
            extractor_link = {
                "source": "Vixcloud",
                "name": "Streaming Community",
                "url": playlist_url,
                "type": "M3U8",
                "referer": referer,
                "quality": QUALITIES_UNKNOWN
            }

            if callback:
                callback(extractor_link)

            return m3u8_content
        except requests.RequestException as e:
            logger.error(f"{TAG} - Errore durante la richiesta HTTP: {e}")
            return None
        except Exception as e:
            logger.error(f"{TAG} - Errore imprevisto: {e}")
            return None

    def _generate_m3u8_content(self, playlist_url, referer):
        """
        Genera il contenuto del file M3U8.

        :param playlist_url: URL della playlist M3U8
        :param referer: Referer della richiesta
        :return: Contenuto del file M3U8 come stringa
        """
        # Intestazione di base per il file M3U8
        m3u8_content = [
            "#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=5000000",
            playlist_url
        ]

        # Aggiungi il referer come commento, se presente
        if referer:
            m3u8_content.insert(0, f"#EXT-X-REFERER:{referer}")

        return "\n".join(m3u8_content)

    def _get_playlist_link(self, url):
        """
        Ottiene il link della playlist dal link dell'iframe.

        :param url: URL dell'iframe
        :return: URL della playlist o None in caso di errore
        """
        TAG = "getPlaylistLink"
        logger.debug(f"{TAG} - Item url: {url}")

        try:
            script = self._get_script(url)
            if not script:
                logger.error(f"{TAG} - Impossibile ottenere lo script")
                return None
            master_playlist = script.get("masterPlaylist")
            if not master_playlist:
                logger.error(f"{TAG} - masterPlaylist non trovato nello script")
                return None
            params = f"token={master_playlist['params']['token']}&expires={master_playlist['params']['expires']}"

            master_playlist_url = master_playlist["url"]
            if "?b" in master_playlist_url:
                master_playlist_url = master_playlist_url.replace("?b:1", "?b=1") + "&" + params
            else:
                master_playlist_url = f"{master_playlist_url}?{params}"

            logger.debug(f"{TAG} - masterPlaylistUrl: {master_playlist_url}")

            if script.get("canPlayFHD"):
                master_playlist_url += "&h=1"

            logger.debug(f"{TAG} - Master Playlist URL: {master_playlist_url}")
            return master_playlist_url
        except Exception as e:
            logger.error(f"{TAG} - Errore durante l'estrazione della playlist: {e}")
            return None

    def _get_script(self, url):
        """
        Estrae e analizza lo script JavaScript contenente i dati della playlist.

        :param url: URL dell'iframe
        :return: Dizionario con i dati dello script o None in caso di errore
        """
        TAG = "getScript"
        logger.debug(f"{TAG} - url: {url}")

        try:
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Host": urlparse(url).netloc,
                "Referer": self.main_url,
                "Sec-Fetch-Dest": "iframe",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "cross-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.debug(f"{TAG} - IFRAME: {soup}")

            scripts = soup.select("script")
            script = next((s for s in scripts if "masterPlaylist" in s.string), None)
            if not script:
                logger.error(f"{TAG} - Nessuno script contenente 'masterPlaylist' trovato")
                return None
            script_data = script.string.replace("\n", "\t")
            script_json = self._get_sanitised_script(script_data)
            logger.debug(f"{TAG} - Script Json: {script_json}")

            script_obj = json.loads(script_json)
            logger.debug(f"{TAG} - Script Obj: {script_obj}")

            return script_obj
        except requests.RequestException as e:
            logger.error(f"{TAG} - Errore durante la richiesta HTTP: {e}")
            return None
        except Exception as e:
            logger.error(f"{TAG} - Errore imprevisto: {e}")
            return None

    def _get_sanitised_script(self, script):
        """
        Pulisce lo script JavaScript per convertirlo in JSON valido.

        :param script: Stringa dello script
        :return: Stringa JSON valida
        """
        return "{" + script.replace("window.video", "\"video\"") \
            .replace("window.streams", "\"streams\"") \
            .replace("window.masterPlaylist", "\"masterPlaylist\"") \
            .replace("window.canPlayFHD", "\"canPlayFHD\"") \
            .replace("params", "\"params\"") \
            .replace("url", "\"url\"") \
            .replace("\"\"url\"\"", "\"url\"") \
            .replace("\"canPlayFHD\"", ",\"canPlayFHD\"") \
            .replace(",\t        }", "}") \
            .replace(",\t            }", "}") \
            .replace("'", "\"") \
            .replace(";", ",") \
            .replace("=", ":") \
            .replace("\\", "") \
            .strip() + "}"

# Esempio di utilizzo
if __name__ == "__main__":
    extractor = StreamingCommunityExtractor()

    def callback(link):
        print(f"Link estratto: {link}")

    # Processa tutte le categorie automaticamente
    m3u8_content = extractor.get_all_categories(referer=MAIN_URL)
    if m3u8_content:
        print(f"Contenuto M3U8 combinato:\n{m3u8_content}")
    else:
        print("Errore: Impossibile generare il file M3U8 per le categorie")