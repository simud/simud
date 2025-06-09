import requests
import json
import os

# URL della lista domini
url = "https://webassistance.github.io/lista-veezie/lista_domini.txt"

# Nome del file W3U
output_dir = "W3U"
output_file = os.path.join(output_dir, "Film.w3u")

try:
    # Crea la directory W3U se non esiste
    os.makedirs(output_dir, exist_ok=True)
    print(f"Directory {output_dir} creata o già esistente.")

    # Scarica il contenuto del file
    print(f"Downloading lista domini da {url}...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # Verifica se la richiesta ha avuto successo
    print("Download completato con successo.")

    # Leggi i domini e rimuovi eventuali righe vuote o commenti
    domains = [line.strip() for line in response.text.splitlines() if line.strip() and not line.startswith('#')]
    print(f"Trovati {len(domains)} domini validi.")

    if not domains:
        raise ValueError("Nessun dominio valido trovato nella lista.")

    # Struttura base del file W3U
    w3u_content = {
        "name": "Film e Serie",
        "author": "Simud",
        "image": "https://play-lh.googleusercontent.com/-BHc2mPj6oRWk0cjwMn5oYSd7rYl5RW1xn8BWdizIHBuh4cBQ6ev_EsxmA4Trt0o2jQ",
        "url": "https://raw.githubusercontent.com/simud/simud/refs/heads/main/W3U/Film.w3u",
        "stations": []
    }
    
    # Aggiungi ogni dominio come una stazione
    for domain in domains:
        # Estrai il nome del dominio e formatta con la prima lettera maiuscola
        domain_name = domain.split('//')[1] if '//' in domain else domain
        domain_name = domain_name.split('/')[0]  # Rimuove eventuali percorsi
        formatted_name = domain_name.split('.')[0].capitalize() + ''.join(domain_name.split('.')[1:])
        
        station = {
            "name": formatted_name,
            "info": "Film e serie streaming",
            "online": "true",
            "image": "https://play-lh.googleusercontent.com/-BHc2mPj6oRWk0cjwMn5oYSd7rYl5RW1xn8BWdizIHBuh4cBQ6ev_EsxmA4Trt0o2jQ",
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Mobile/15E148 Safari/605.1.15/Clipbox+/2.2.8",
            "referer": domain,
            "url": domain,
            "embed": "true",
            "isHost": ""
        }
        w3u_content["stations"].append(station)
    
    # Scrivi il file W3U
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(w3u_content, f, indent=2, ensure_ascii=False)
    
    print(f"File W3U '{output_file}' creato con successo!")

except requests.RequestException as e:
    print(f"Errore nel download della lista: {e}")
    raise
except Exception as e:
    print(f"Errore durante l'esecuzione: {e}")
    raise
