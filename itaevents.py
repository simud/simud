import xml.etree.ElementTree as ET
import random
import uuid
import fetcher
import json
import os
import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import quote_plus

# Costanti
NUMERO_CANALI = 10000
FILE_JSON_DADDY = "daddyliveSchedule.json"
FILE_OUTPUT_M3U8 = "itaevents.m3u8"
LOGO = "https://raw.githubusercontent.com/cribbiox/eventi/refs/heads/main/ddsport.png"
CACHE_LOGO = {}

PAROLE_CHIAVE_EVENTI = ["italy", "atp", "tennis", "formula uno", "f1", "motogp", "moto gp", "volley", "serie a", "serie b", "serie c", "uefa champions", "uefa europa",
                       "conference league", "coppa italia"]

# Intestazioni HTTP predefinite con i nuovi valori
INTESTAZIONI_DEFAULT = {
    "Accept": "*/*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,ru;q=0.5",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://dokoplay.xyz",
    "Referer": "https://dokoplay.xyz/"
}

# Archiviazione metadati dei canali
METADATI_CANALI = []

# Rimuovi il file M3U8 esistente se presente
if os.path.exists(FILE_OUTPUT_M3U8):
    os.remove(FILE_OUTPUT_M3U8)

def get_dynamic_logo(nome_evento):
    # ... (mantenuta la funzione get_dynamic_logo originale, traduci i commenti se necessario)
    pass

def genera_id_univoci(conteggio, seme=42):
    """Genera una lista di ID univoci"""
    random.seed(seme)
    return [str(uuid.UUID(int=random.getrandbits(128))) for _ in range(conteggio)]

def carica_json(percorso_file):
    """Carica i dati JSON dal file specificato"""
    with open(percorso_file, 'r', encoding='utf-8') as file:
        return json.load(file)

def ottieni_link_stream(id_dlhd, nome_evento="", nome_canale="", max_riprova=3):
    """Ottiene il link dello stream per il canale specificato"""
    print(f"Ottenendo link stream per ID canale: {id_dlhd} - {nome_evento} su {nome_canale}...")
    timeout_base = 10
    metadati = {
        "id_canale": id_dlhd,
        "nome_evento": nome_evento,
        "nome_canale": nome_canale,
        "origine": INTESTAZIONI_DEFAULT["Origin"],
        "referrer": INTESTAZIONI_DEFAULT["Referer"],
        "user_agent": INTESTAZIONI_DEFAULT["User-Agent"]
    }

    for tentativo in range(max_riprova):
        try:
            risposta = requests.get(
                f"https://daddylive.mp/embed/stream-{id_dlhd}.php",
                headers=INTESTAZIONI_DEFAULT,
                timeout=timeout_base
            )
            risposta.raise_for_status()
            soup = BeautifulSoup(risposta.text, 'html.parser')
            iframe = soup.find('iframe', id='thatframe')

            if iframe and iframe.get('src'):
                link_reale = iframe.get('src')
                dominio_sito_padre = link_reale.split('/premiumtv')[0]
                link_chiave_server = f'{dominio_sito_padre}/server_lookup.php?channel_id=premium{id_dlhd}'
                
                intestazioni_chiave = INTESTAZIONI_DEFAULT.copy()
                intestazioni_chiave["Referer"] = f"https://newembedplay.xyz/premiumtv/daddylivehd.php?id={id_dlhd}"
                intestazioni_chiave["Origin"] = "https://newembedplay.xyz"

                risposta_chiave = requests.get(
                    link_chiave_server,
                    headers=intestazioni_chiave,
                    timeout=timeout_base
                )
                risposta_chiave.raise_for_status()
                dati_chiave_server = risposta_chiave.json()

                if 'server_key' in dati_chiave_server:
                    chiave_server = dati_chiave_server['server_key']
                    url_stream = f"https://{chiave_server}new.newkso.ru/{chiave_server}/premium{id_dlhd}/mono.m3u8"
                    metadati["url_stream"] = url_stream
                    METADATI_CANALI.append(metadati)
                    return url_stream

            if tentativo < max_riprova - 1:
                tempo_attesa = (2 ** tentativo) + random.uniform(0, 1)
                time.sleep(tempo_attesa)
                
        except Exception as e:
            print(f"Errore in ottieni_link_stream (tentativo {tentativo+1}/{max_riprova}): {e}")
            if tentativo < max_riprova - 1:
                time.sleep((2 ** tentativo) + random.uniform(0, 1))
            continue

    return None

def pulisci_titolo_gruppo(chiave_sport):
    """Pulisce la chiave dello sport per creare un titolo di gruppo appropriato"""
    return re.sub(r'<[^>]+>', '', chiave_sport).strip().title()

def deve_includere_canale(nome_canale, nome_evento, chiave_sport):
    """Verifica se il canale deve essere incluso in base alle parole chiave"""
    testo_combinato = (nome_canale + " " + nome_evento + " " + chiave_sport).lower()
    return any(parola.lower() in testo_combinato for parola in PAROLE_CHIAVE_EVENTI)

def processa_eventi():
    """Processa gli eventi e genera il file M3U8"""
    dadjson = carica_json(FILE_JSON_DADDY)
    totale_eventi = 0
    eventi_saltati = 0
    canali_filtrati = 0
    canali_processati = 0

    categorie_escluse = [
        "TV Shows", "Cricket", "Aussie rules", "Snooker", "Baseball",
        "Biathlon", "Cross Country", "Horse Racing", "Ice Hockey",
        "Waterpolo", "Golf", "Darts", "Cycling"
    ]

    id_univoci = genera_id_univoci(NUMERO_CANALI)

    with open(FILE_OUTPUT_M3U8, 'w', encoding='utf-8') as file:
        file.write('#EXTM3U\n')

    for giorno, dati_giorno in dadjson.items():
        for chiave_sport, eventi_sport in dati_giorno.items():
            chiave_sport_pulita = pulisci_titolo_gruppo(chiave_sport)
            totale_eventi += len(eventi_sport)

            if chiave_sport_pulita in categorie_escluse:
                eventi_saltati += len(eventi_sport)
                continue

            for partita in eventi_sport:
                for canale in partita.get("channels", []):
                    try:
                        # Elaborazione della data
                        giorno_pulito = re.sub(r'(\d+)(st|nd|rd|th)| - Schedule Time UK GMT', r'\1', giorno).strip()
                        parti_giorno = giorno_pulito.split()
                        
                        if len(parti_giorno) >= 3:
                            numero_giorno = parti_giorno[-3] if parti_giorno[-3].isdigit() else datetime.datetime.now(pytz.timezone('Europe/Rome')).strftime('%d')
                            nome_mese = parti_giorno[-2]
                            anno = parti_giorno[-1]
                        else:
                            ora = datetime.datetime.now(pytz.timezone('Europe/Rome'))
                            numero_giorno, nome_mese, anno = ora.strftime('%d'), ora.strftime('%B'), ora.strftime('%Y')

                        orario_str = partita.get("time", "00:00")
                        ora, minuto = map(int, orario_str.split(":"))
                        ora_cet = (ora + 2) % 24
                        orario_cet_str = f"{ora_cet:02d}:{minuto}"

                        mappa_mesi = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
                                    "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"}
                        numero_mese = mappa_mesi.get(nome_mese, "01")
                        numero_giorno = f"0{numero_giorno}" if len(str(numero_giorno)) == 1 else numero_giorno
                        anno_corto = anno[-2:]
                        data_ora_formattata = f"{numero_giorno}/{numero_mese}/{anno_corto} - {orario_cet_str}"

                        nome_canale = canale["channel_name"] if isinstance(canale, dict) and "channel_name" in canale else str(canale)
                        nome_evento = partita["event"].split(":")[0].strip() if ":" in partita["event"] else partita["event"]
                        dettagli_evento = partita["event"]

                        if deve_includere_canale(nome_canale, nome_evento, chiave_sport):
                            id_canale = canale.get("channel_id", str(uuid.uuid4()))
                            url_stream = ottieni_link_stream(id_canale, dettagli_evento, nome_canale)

                            if url_stream:
                                with open(FILE_OUTPUT_M3U8, 'a', encoding='utf-8') as file:
                                    nome_tvg = f"{orario_cet_str} {dettagli_evento} - {numero_giorno}/{numero_mese}/{anno_corto}"
                                    logo_evento = get_dynamic_logo(partita["event"])
                                    
                                    file.write(f'#EXTINF:-1 tvg-id="{nome_evento} - {dettagli_evento.split(":", 1)[1].strip() if ":" in dettagli_evento else dettagli_evento}" '
                                             f'tvg-name="{nome_tvg}" tvg-logo="{logo_evento}" group-title="{chiave_sport_pulita}", {nome_canale}\n')
                                    file.write(f'#EXTVLCOPT:http-referrer={INTESTAZIONI_DEFAULT["Referer"]}\n')
                                    file.write(f'#EXTVLCOPT:http-user-agent={INTESTAZIONI_DEFAULT["User-Agent"]}\n')
                                    file.write(f'#EXTVLCOPT:http-origin={INTESTAZIONI_DEFAULT["Origin"]}\n')
                                    file.write(f"{url_stream}\n\n")

                                canali_processati += 1
                                canali_filtrati += 1

                    except Exception as e:
                        print(f"Errore durante l'elaborazione del canale: {e}")
                        continue

    # Salva i metadati in un file JSON
    with open("metadati_canali.json", 'w', encoding='utf-8') as f:
        json.dump(METADATI_CANALI, f, indent=2)

    print(f"\n=== Riepilogo Elaborazione ===")
    print(f"Totale eventi: {totale_eventi}")
    print(f"Eventi saltati: {eventi_saltati}")
    print(f"Canali filtrati: {canali_filtrati}")
    print(f"Canali processati: {canali_processati}")
    print(f"Metadati salvati in metadati_canali.json")
    return canali_processati

def main():
    """Funzione principale"""
    totale_processati = processa_eventi()
    print(f"File M3U8 generato con {totale_processati} canali" if totale_processati > 0 else "Nessun canale valido trovato")

if __name__ == "__main__":
    main()
