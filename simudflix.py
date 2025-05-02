# it/dogior/hadEnough/streaming_community_extractor.py

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
MAIN_URL = "https://streamingcommunity.spa"  # Sostituisci con l'URL corretto
NAME = "Streaming Community"
QUALITIES_UNKNOWN = 0  # Valore per qualità sconosciuta
M3U8_OUTPUT_FILE = "streaming.m3u8"  # Nome del file M3U8 generato

class StreamingCommunityExtractor:
    def __init__(self):
        self.main_url = MAIN_URL
        self.name = NAME
        self.requires_referer = False

    def get_url(self, url, referer=None, subtitle_callback=None, callback=None, output_file=M3U8_OUTPUT_FILE):
        """
        Estrae i link di streaming da un URL dato e genera un file M3U8.

        :param url: URL della pagina
        :param referer: Referer della richiesta (opzionale)
        :param subtitle_callback: Funzione di callback per i sottotitoli
        :param callback: Funzione di callback per i link estratti
        :param output_file: Nome del file M3U8 da generare (default: streaming.m3u8)
        :return: Contenuto del file M3U8 come stringa
        """
        TAG = "GetUrl"
        logger.debug(f"{TAG} - REFERER: {referer} URL: {url}")

        if not url:
            return None

        # Effettua la richiesta alla pagina
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        iframe_src = soup.select_one("iframe")["src"]
        playlist_url = self._get_playlist_link(iframe_src)
        logger.warning(f"{TAG} - FINAL URL: {playlist_url}")

        # Crea il contenuto del file M3U8
        m3u8_content = self._generate_m3u8_content(playlist_url, referer)
        
        # Salva il file M3U8
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(m3u8_content)
        logger.info(f"{TAG} - File M3U8 salvato come: {output_file}")

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

    def _generate_m3u8_content(self, playlist_url, referer):
        """
        Genera il contenuto del file M3U8.

        :param playlist_url: URL della playlist M3U8
        :param referer: Referer della richiesta
        :return: Contenuto del file M3U8 come stringa
        """
        # Intestazione di base per il file M3U8
        m3u8_content = [
            "#EXTM3U",
            f"#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=5000000",
            playlist_url
        ]

        # Aggiungi il referer come commento, se presente
        if referer:
            m3u8_content.insert(1, f"#EXT-X-REFERER:{referer}")

        return "\n".join(m3u8_content)

    def _get_playlist_link(self, url):
        """
        Ottiene il link della playlist dal link dell'iframe.

        :param url: URL dell'iframe
        :return: URL della playlist
        """
        TAG = "getPlaylistLink"
        logger.debug(f"{TAG} - Item url: {url}")

        script = self._get_script(url)
        master_playlist = script["masterPlaylist"]
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

    def _get_script(self, url):
        """
        Estrae e analizza lo script JavaScript contenente i dati della playlist.

        :param url: URL dell'iframe
        :return: Dizionario con i dati dello script
        """
        TAG = "getScript"
        logger.debug(f"{TAG} - url: {url}")

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Host": urlparse(url).netloc,
            "Referer": self.main_url,
            "Sec-Fetch-Dest": "iframe",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.debug(f"{TAG} - IFRAME: {soup}")

        scripts = soup.select("script")
        script = next(s for s in scripts if "masterPlaylist" in s.string).string.replace("\n", "\t")
        script_json = self._get_sanitised_script(script)
        logger.debug(f"{TAG} - Script Json: {script_json}")

        script_obj = json.loads(script_json)
        logger.debug(f"{TAG} - Script Obj: {script_obj}")

        return script_obj

    def _get_sanitised_script(self, script):
        podvrščina JavaScript za čiščenje
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

    # Sostituisci con un URL valido
    test_url = "https://streamingcommunity.spa/example"
    m3u8_content = extractor.get_url(test_url, referer=MAIN_URL, callback=callback)
    if m3u8_content:
        print(f"Contenuto M3U8:\n{m3u8_content}")