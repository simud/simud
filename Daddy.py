import requests

def concatena_m3u8_con_epg():
    # Lista degli URL M3U8
    url_m3u8 = [
        "https://raw.githubusercontent.com/simud/simud/refs/heads/main/sportstreaming_playlist.m3u8",
        "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/daddylive-channels.m3u8",
        "https://raw.githubusercontent.com/simud/simud/refs/heads/main/twitch_streams.m3u8",
        "https://raw.githubusercontent.com/Brenders/Pluto-TV-Italia-M3U/refs/heads/main/PlutoItaly.m3u"
        # Aggiungi altri URL M3U8 qui, fino a un massimo di 10
        # Esempio: "https://example.com/playlist.m3u8",
    ]
    
    # Lista degli URL EPG (opzionale)
    url_epg = [
        "http://www.epgitalia.tv/gzip,http://epg-guide.com/it.gz",
        "https://raw.github.com/matthuisman/i.mjh.nz/master/PlutoTV/us.xml.gz",
        "https://github.com/matthuisman/i.mjh.nz/raw/master/PlutoTV/it.xml.gz",
        "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/epgs/daddylive-events-epg.xml",
        "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/epgs/daddylive-channels-epg.xml",
        "https://github.com/matthuisman/i.mjh.nz/raw/master/SamsungTVPlus/it.xml.gz"
        # Aggiungi qui gli URL EPG, fino a un massimo di 10
        # Esempio: "https://example.com/epg1.xml",
        # "https://example.com/epg2.xml",
    ]
    
    # Verifica il limite di 10 per ciascuna lista
    if len(url_m3u8) > 10:
        print(f"Errore: Sono stati definiti {len(url_m3u8)} URL M3U8, ma il massimo è 10.")
        return
    if len(url_epg) > 10:
        print(f"Errore: Sono stati definiti {len(url_epg)} URL EPG, ma il massimo è 10.")
        return
    
    # Crea i contenuti combinati
    lista_m3u8_combinata = ["#EXTM3U"]
    lista_epg_combinata = []
    epg_presente = False
    
    # Processa gli URL M3U8
    for url in url_m3u8:
        try:
            print(f"Tentativo di scaricare M3U8: {url}")
            risposta = requests.get(url, timeout=10)
            risposta.raise_for_status()
            righe = risposta.text.splitlines()
            print(f"Scaricate {len(righe)} righe da {url}")
            for riga in righe:
                riga = riga.strip()
                if riga and riga != "#EXTM3U":
                    lista_m3u8_combinata.append(riga)
        except requests.RequestException as e:
            print(f"Errore nel scaricare {url}: {str(e)}")
            return
    
    # Processa gli URL EPG (se presenti)
    for url in url_epg:
        try:
            print(f"Tentativo di scaricare EPG: {url}")
            risposta = requests.get(url, timeout=10)
            risposta.raise_for_status()
            contenuto_epg = risposta.text
            lista_epg_combinata.append(contenuto_epg)
            epg_presente = True
            print(f"EPG scaricato con successo da {url}")
        except requests.RequestException as e:
            print(f"Errore nel scaricare EPG {url}: {str(e)}")
            return
    
    # Salva il file M3U8 combinato
    try:
        with open("lista_combinata.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(lista_m3u8_combinata))
        print(f"File M3U8 creato con successo: lista_combinata.m3u8 con {len(lista_m3u8_combinata)} righe")
    except Exception as e:
        print(f"Errore nella creazione del file M3U8: {str(e)}")
        return
    
    # Salva il file EPG combinato (se presente)
    if epg_presente:
        try:
            with open("epg_combinato.xml", "w", encoding="utf-8") as f:
                # Inizio file XML
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
                f.write('<tv>\n')
                
                # Aggiunge ogni contenuto EPG
                for epg in lista_epg_combinata:
                    f.write(epg)
                
                # Fine file XML
                f.write('</tv>\n')
            print("File EPG creato con successo: epg_combinato.xml")
        except Exception as e:
            print(f"Errore nella creazione del file EPG: {str(e)}")

if __name__ == "__main__":
    concatena_m3u8_con_epg()
