import re
import base64
import requests
from bs4 import BeautifulSoup
import os
import time
import html
from urllib.parse import urljoin

# Funzioni per estrarre i link e le chiavi
def extract_channel_links(main_url):
    """Estrae tutti i link ai canali dalla pagina principale"""
    try:
        response = requests.get(main_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        channel_links = []
        
        # Cerca tutti i link nei pulsanti
        buttons = soup.find_all('button', class_='btn')
        for button in buttons:
            a_tag = button.find('a')
            if a_tag and 'href' in a_tag.attrs:
                href = a_tag['href'].strip()
                # Rimuovi eventuali spazi e apici
                href = re.sub(r'[`\'"]', '', href).strip()
                if href.startswith('http'):
                    channel_links.append(href)
                elif href:
                    # Costruisci URL completo se è relativo
                    channel_links.append(urljoin(main_url, href))
        
        return channel_links
    except Exception as e:
        print(f"Errore durante l'estrazione dei link dei canali: {e}")
        return []

def extract_clappr_keys(url):
    """Estrae il link MPD e le chiavi dal player Clappr"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Cerca il source MPD
        mpd_match = re.search(r'source:\s*[\'"]([^\'"\s]+\.mpd)[\'"]', response.text)
        if not mpd_match:
            print(f"Nessun link MPD trovato nella pagina Clappr {url}")
            return None, None, None
        
        mpd_link = mpd_match.group(1).strip()
        
        # Cerca le clearKeys
        keys_match = re.search(r'clearKeys:\s*{\s*[\'"]([^\'"]+)[\'"]:\s*[\'"]([^\'"]+)[\'"]', response.text)
        if not keys_match:
            print(f"Nessuna chiave trovata nella pagina Clappr {url}")
            return mpd_link, None, None
        
        key_id = keys_match.group(1).strip()
        key = keys_match.group(2).strip()
        
        return mpd_link, key_id, key
    except Exception as e:
        print(f"Errore durante l'estrazione delle chiavi Clappr da {url}: {e}")
        return None, None, None

def extract_mpd_link_from_page(url):
    """Estrae il link MPD da una pagina HTML che contiene un iframe con player.html#"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        iframe = soup.find('iframe')
        
        if iframe and 'src' in iframe.attrs:
            src = iframe['src']
            # Cerca il pattern player.html# seguito dal link MPD
            match = re.search(r'player\.html#(https?://.+?)(?="|\'|\s|$)', src)
            if match:
                # Decodifica le entità HTML come &
                mpd_url = html.unescape(match.group(1))
                return mpd_url
        
        # Se non troviamo il link nell'iframe, cerchiamo in tutto l'HTML
        match = re.search(r'player\.html#(https?://.+?)(?="|\'|\s|$)', response.text)
        if match:
            mpd_url = html.unescape(match.group(1))
            return mpd_url
            
        print(f"Nessun link MPD trovato nella pagina {url}.")
        return None
    except Exception as e:
        print(f"Errore durante l'estrazione del link MPD da {url}: {e}")
        return None

def decode_base64_keys(encoded_string):
    """Decodifica una stringa base64 e restituisce le due chiavi separate da ':'"""
    try:
        decoded = base64.b64decode(encoded_string).decode('utf-8')
        if ':' in decoded:
            key_id, key = decoded.split(':', 1)
            return key_id, key
        else:
            print("La stringa decodificata non contiene il separatore ':'")
            return None, None
    except Exception as e:
        print(f"Errore durante la decodifica base64: {e}")
        return None, None

def process_channel_page(url):
    """Processa una pagina di canale e restituisce il nome e i dati del flusso"""
    channel_name = url.split('/')[-1].replace('.htm', '')
    print(f"\nProcessando il canale: {channel_name}")
    
    # Prova prima il metodo Clappr
    mpd_link, key_id, key = extract_clappr_keys(url)
    if mpd_link and key_id and key:
        print(f"Generato flusso MPD con chiavi Clappr per {channel_name}")
        return channel_name, mpd_link, key_id, key
    
    # Se Clappr fallisce, prova il metodo con ck=
    mpd_url = extract_mpd_link_from_page(url)
    if mpd_url:
        ck_match = re.search(r'[?&]ck=([^&\s]+)', mpd_url)
        if ck_match:
            encoded_keys = ck_match.group(1)
            key_id, key = decode_base64_keys(encoded_keys)
            if key_id and key:
                print(f"Generato flusso MPD con chiavi ck= per {channel_name}")
                return channel_name, mpd_url.split('?ck=')[0], key_id, key
            else:
                print(f"Impossibile decodificare le chiavi ck= per {channel_name}")
        else:
            print(f"Nessun parametro 'ck' trovato nell'URL MPD per {channel_name}")
    
    print(f"Impossibile ottenere flusso MPD con chiavi per {channel_name}")
    return channel_name, None, None, None

# Associazioni per tvg-name, tvg-id, group-title e logo
channel_associations = {
    "euro1": "EuroSport 1",
    "skyuno": "Sky UNO",
    "skyunohd": "Sky UNO",
    "tennis": "Sky Sport Tennis",
    "tennishd": "Sky Sport Tennis",
    "dazn1hd": "DAZN 1",
    "motogp": "Sky Sport MotoGP",
    "motogphd": "Sky Sport MotoGP",
    "f1": "Sky Sport F1",
    "f1hd": "Sky Sport F1",
    "max": "Sky Sport Football",
    "maxhd": "Sky Sport Football",
    "arena": "Sky Sport Arena",
    "arenahd": "Sky Sport Arena",
    "calcio": "Sky Sport Calcio",
    "calciohd": "Sky Sport Calcio",
    "uno": "Sky Sport UNO",
    "unohd": "Sky Sport UNO",
    "sport24hd": "Sky Sport 24",
    "nba": "Sky Sport NBA",
    "nbahd": "Sky Sport NBA"
}

tvg_id_associations = {
    "EuroSport 1": "eurosport1.it",
    "Sky UNO": "skyuno.it",
    "Sky Sport Tennis": "skysporttennis.it",
    "DAZN 1": "dazn1.it",
    "Sky Sport MotoGP": "skysportmotogp.it",
    "Sky Sport F1": "skysportf1.it",
    "Sky Sport Football": "skysportmax.it",
    "Sky Sport Arena": "skysportarena.it",
    "Sky Sport Calcio": "skysportcalcio.it",
    "Sky Sport UNO": "skysportuno.it",
    "Sky Sport 24": "Sky.Sport24.it",
    "Sky Sport NBA": "skysportnba.it"
}

group_title_associations = {
    "EuroSport 1": "Dazn MPD",
    "Sky UNO": "Intrattenimento",
    "Sky Sport Tennis": "Dazn MPD",
    "DAZN 1": "Dazn MPD",
    "Sky Sport MotoGP": "Dazn MPD",
    "Sky Sport F1": "Dazn MPD",
    "Sky Sport Football": "Dazn MPD",
    "Sky Sport Arena": "Dazn MPD",
    "Sky Sport Calcio": "Dazn MPD",
    "Sky Sport UNO": "Dazn MPD",
    "Sky Sport 24": "Dazn MPD",
    "Sky Sport NBA": "Dazn MPD"
}

logo_associations = {
    "EuroSport 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/spain/eurosport-1-es.png",
    "Sky UNO": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-uno-it.png",
    "Sky Sport Tennis": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-tennis-it.png",
    "DAZN 1": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/DAZN_1_Logo.svg/774px-DAZN_1_Logo.svg.png",
    "Sky Sport MotoGP": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-motogp-it.png",
    "Sky Sport F1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-f1-it.png",
    "Sky Sport Football": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-football-it.png",
    "Sky Sport Arena": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-arena-it.png",
    "Sky Sport Calcio": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-calcio-it.png",
    "Sky Sport UNO": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-uno-it.png",
    "Sky Sport 24": "https://i.postimg.cc/d3fXKnGj/sky-condivisione.png",
    "Sky Sport NBA": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-nba-it.png"
}

def get_channel_info(channel_name):
    """Ottiene le informazioni del canale in base al nome"""
    tvg_name = channel_associations.get(channel_name, channel_name)
    tvg_id = tvg_id_associations.get(tvg_name, "")
    group_title = group_title_associations.get(tvg_name, "Altro")
    logo = logo_associations.get(tvg_name, "")
    
    return {
        "tvg_id": tvg_id,
        "tvg_name": tvg_name,
        "tvg_logo": logo,
        "group_title": group_title,
        "suffix": ""  # Imposta il suffisso come vuoto per rimuovere (H) o (Hd)
    }

def create_m3u_entry(channel_name, mpd_url, key_id, key):
    """Crea una voce M3U per il canale nel formato richiesto"""
    info = get_channel_info(channel_name)
    
    extinf = f'#EXTINF:-1 tvg-id="{info["tvg_id"]}" tvg-logo="{info["tvg_logo"]}" group-title="{info["group_title"]}",{info["tvg_name"]}'
    kodiprop_license_type = '#KODIPROP:inputstream.adaptive.license_type=clearkey'
    kodiprop_license_key = f'#KODIPROP:inputstream.adaptive.license_key={key_id}:{key}'
    
    return f"{extinf}\n{kodiprop_license_type}\n{kodiprop_license_key}\n{mpd_url}\n"

def remove_duplicate_channels(m3u_file):
    """Legge il file M3U, rimuove i doppioni basati sull'URL MPD e riscrive il file"""
    try:
        with open(m3u_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Inizializza variabili per parsing
        entries = []
        current_entry = []
        current_mpd = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#EXTINF'):
                if current_entry and current_mpd:
                    entries.append((current_mpd, current_entry))
                current_entry = [line]
                current_mpd = None
            elif line.startswith('#KODIPROP'):
                current_entry.append(line)
            elif line.startswith('http') and line.endswith('.mpd'):
                current_mpd = line
                current_entry.append(line)
            else:
                current_entry.append(line)
        
        # Aggiungi l'ultima voce
        if current_entry and current_mpd:
            entries.append((current_mpd, current_entry))
        
        # Identifica gli URL MPD unici e mantieni la prima voce
        seen_mpds = set()
        unique_entries = []
        for mpd_url, entry in entries:
            if mpd_url not in seen_mpds:
                seen_mpds.add(mpd_url)
                unique_entries.append(entry)
        
        # Riscrivi il file M3U con le voci uniche
        with open(m3u_file, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for entry in unique_entries:
                f.write('\n'.join(entry) + '\n')
        
        print(f"Rimossi i doppioni. File M3U aggiornato con {len(unique_entries)} canali unici: {m3u_file}")
        return True
    except Exception as e:
        print(f"Errore durante la rimozione dei doppioni nel file M3U: {e}")
        return False

def add_channels_to_m3u(channels, m3u_file="hat.m3u8"):
    """Aggiunge i canali al file M3U nella directory corrente"""
    # Crea o sovrascrivi il file M3U nella directory corrente
    with open(m3u_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
    print(f"Creato nuovo file M3U: {m3u_file}")
    
    new_entries = []
    for channel_name, (mpd_url, key_id, key) in channels.items():
        entry = create_m3u_entry(channel_name, mpd_url, key_id, key)
        new_entries.append(entry)
    
    with open(m3u_file, 'a', encoding='utf-8') as f:
        f.write("\n# Canali aggiunti da Hattrick\n")
        for entry in new_entries:
            f.write(entry)
    
    print(f"Aggiunti {len(new_entries)} canali al file M3U: {m3u_file}")
    
    # Rimuovi i doppioni
    remove_duplicate_channels(m3u_file)
    return True

def main():
    main_url = "https://hattrick.ws/"
    
    print(f"Estraendo i link dei canali da {main_url}...")
    channel_links = extract_channel_links(main_url)
    print(f"Trovati {len(channel_links)} link a canali.")
    
    results = {}
    for i, url in enumerate(channel_links):
        print(f"Processando {i+1}/{len(channel_links)}: {url}")
        channel_name, mpd_url, key_id, key = process_channel_page(url)
        if mpd_url and key_id and key:
            results[channel_name] = (mpd_url, key_id, key)
        else:
            print(f"Impossibile generare flusso MPD per {channel_name}")
        
        time.sleep(1)
    
    print(f"\nAggiungendo i canali al file M3U: hat.m3u8...")
    if add_channels_to_m3u(results):
        print(f"Canali aggiunti con successo al file M3U!")
    else:
        print(f"Errore durante l'aggiunta dei canali al file M3U.")

if __name__ == "__main__":
    main()
