import requests
from github import Github
import os

# URL della lista IPTV da filtrare
IPTV_URL = "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/main/daddylive-events.m3u8"

# Parole chiave per identificare eventi italiani
PAROLE_CHIAVE_ITALIANE = [
    "italy", "italia", "serie a", "serie b", "coppa italia", "juventus", "inter", "milan",
    "napoli", "roma", "lazio", "fiorentina", "atalanta", "torino", "bologna", "lecce"
]

# Nome dei file filtrati
FILE_ITALIANO = "eventi_italiani.m3u8"
FILE_STRANIERO = "eventi_stranieri.m3u8"

# Ottieni il token GitHub dalle variabili d'ambiente
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "pigzillaaaaa"
REPO_NAME = "iptv-scraper"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/"

def scarica_lista():
    """Scarica la lista IPTV e la divide in eventi italiani e stranieri"""
    try:
        response = requests.get(IPTV_URL)
        response.raise_for_status()
        righe = response.text.splitlines()
    except requests.RequestException as e:
        print(f"Errore durante il download della lista IPTV: {e}")
        return None, None

    eventi_italiani = []
    eventi_stranieri = []

    for i in range(len(righe)):
        if "#EXTINF" in righe[i]:
            evento = righe[i] + "\n" + righe[i + 1] if i + 1 < len(righe) else ""
            if any(keyword.lower() in evento.lower() for keyword in PAROLE_CHIAVE_ITALIANE):
                eventi_italiani.append(evento)
            else:
                eventi_stranieri.append(evento)

    return "\n".join(eventi_italiani), "\n".join(eventi_stranieri)


def aggiorna_file_raw(contenuto_italiano, contenuto_straniero):
    """Aggiorna i file RAW su GitHub"""
    if not GITHUB_TOKEN:
        print("Errore: Token GitHub non trovato!")
        return

    try:
        # Imposta l'header per l'autenticazione
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }

        # URL per i file raw
        file_italiano_url = f"{RAW_BASE_URL}{FILE_ITALIANO}"
        file_straniero_url = f"{RAW_BASE_URL}{FILE_STRANIERO}"

        # Effettua la richiesta di aggiornamento del file raw (con PUT)
        response_italiano = requests.put(file_italiano_url, headers=headers, data=contenuto_italiano)
        response_straniero = requests.put(file_straniero_url, headers=headers, data=contenuto_straniero)

        if response_italiano.status_code == 200 and response_straniero.status_code == 200:
            print("✅ File RAW aggiornati con successo!")
        else:
            print(f"Errore durante l'aggiornamento dei file RAW: {response_italiano.text}")
            print(f"Errore durante l'aggiornamento dei file RAW: {response_straniero.text}")
    
    except Exception as e:
        print(f"Errore durante l'aggiornamento: {e}")


if __name__ == "__main__":
    eventi_ita, eventi_str = scarica_lista()
    if eventi_ita is not None and eventi_str is not None:
        aggiorna_file_raw(eventi_ita, eventi_str)


if __name__ == "__main__":
    eventi_ita, eventi_str = scarica_lista()
    if eventi_ita is not None and eventi_str is not None:
        aggiorna_repo(eventi_ita, eventi_str)
