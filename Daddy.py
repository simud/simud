import requests

def concatena_m3u8_con_epg():
    # Lista degli URL M3U8
    url_m3u8 = [
        "https://raw.githubusercontent.com/simud/simud/refs/heads/main/sportstreaming_playlist.m3u8",
        "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/daddylive-channels.m3u8",
        "https://raw.githubusercontent.com/simud/simud/refs/heads/main/twitch_streams.m3u8",
        "https://raw.githubusercontent.com/Brenders/Pluto-TV-Italia-M3U/refs/heads/main/PlutoItaly.m3u"
        # Aggiungi altri URL M3U8 qui, fino a un massimo di 10
    ]
    
    # Lista degli URL EPG
    url_epg = [
        "http://www.epgitalia.tv/gzip",
        "http://epg-guide.com/it.gz",
        "https://raw.github.com/matthuisman/i.mjh.nz/master/PlutoTV/us.xml.gz",
        "https://github.com/matthuisman/i.mjh.nz/raw/master/PlutoTV/it.xml.gz",
        "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/epgs/daddylive-events-epg.xml",
        "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/epgs/daddylive-channels-epg.xml",
        "https://github.com/matthuisman/i.mjh.nz/raw/master/SamsungTVPlus/it.xml.gz"
        # Aggiungi altri URL EPG qui, fino a un massimo di 10
    ]
    
    # Verifica il limite di 10 per ciascuna lista
    if len(url_m3u8) > 10:
        print(f"Errore: Sono stati definiti {len(url_m3u8)} URL M3U8, ma il massimo è 10.")
        return
    if len(url_epg) > 10:
        print(f"Errore: Sono stati definiti {len(url_epg)} URL EPG, ma il massimo è 10.")
        return
    
    # Crea il contenuto combinato M3U8
    lista_m3u8_combinata = []
    
    # Aggiungi la riga #EXTM3U con url-tvg se ci sono EPG
    if url_epg:
        epg_string = ",".join(url_epg)
        lista_m3u8_combinata.append(f'#EXTM3U url-tvg="{epg_string}"')
    else:
        lista_m3u8_combinata.append("#EXTM3U")
    
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
    
    # Salva il file M3U8 combinato
    try:
        with open("lista_combinata.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(lista_m3u8_combinata))
        print(f"File M3U8 creato con successo: lista_combinata.m3u8 con {len(lista_m3u8_combinata)} righe")
    except Exception as e:
        print(f"Errore nella creazione del file M3U8: {str(e)}")
        return

if __name__ == "__main__":
    concatena_m3u8_con_epg()
