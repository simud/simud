import requests

def concatenate_m3u8():
    # Lista per gli URL
    urls = []
    max_urls = 10
    
    # Precarica i due URL richiesti
    urls.append("https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/daddylive-channels.m3u8")
    urls.append("https://raw.githubusercontent.com/simud/simud/refs/heads/main/sportstreaming_playlist.m3u8")
    
    # Chiedi ulteriori URL all'utente
    print("I seguenti URL sono già inclusi:")
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
    print(f"\nPuoi aggiungere altri URL (max {max_urls - len(urls)} aggiuntivi). Premi Invio senza testo per terminare.")
    
    while len(urls) < max_urls:
        url = input(f"URL {len(urls) + 1}: ").strip()
        if not url:  # Se l'input è vuoto, termina
            break
        urls.append(url)
    
    # Crea il contenuto combinato
    combined_content = ["#EXTM3U"]
    
    # Processa ogni URL
    for url in urls:
        try:
            print(f"Tentativo di scaricare: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            lines = response.text.splitlines()
            print(f"Scaricate {len(lines)} righe da {url}")
            for line in lines:
                line = line.strip()
                if line and line != "#EXTM3U":
                    combined_content.append(line)
        except requests.RequestException as e:
            print(f"Errore nel scaricare {url}: {str(e)}")
            return
    
    # Salva il file localmente
    try:
        with open("combined_playlist.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(combined_content))
        print(f"File creato con successo: combined_playlist.m3u8 con {len(combined_content)} righe")
    except Exception as e:
        print(f"Errore nella creazione del file: {str(e)}")

if __name__ == "__main__":
    concatenate_m3u8()
