import requests
from github import Github
import os

# URL della lista IPTV da filtrare (rimane nel repository pigzillaaaaa/iptv-scraper)
IPTV_URL = "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/main/daddylive-events.m3u8"

# Parole chiave per identificare eventi italiani
PAROLE_CHIAVE_ITALIANE = [
    "italy", "italia", "serie a", "serie b", "coppa italia", "juventus", "inter", "milan",
    "napoli", "roma", "lazio", "fiorentina", "atalanta", "torino", "bologna", "lecce"
]

# Nome dei file da aggiornare nel repository simud
FILE_ITALIANO = "eventi_italiani.m3u8"
FILE_STRANIERO = "eventi_stranieri.m3u8"

# Token GitHub e repository di destinazione (simud)
GITHUB_TOKEN = os.getenv("GH_TOKEN")  # Usa GH_TOKEN come nel tuo workflow
REPO_OWNER = "pigzillaaaaa"           # Sostituisci con il tuo username, se diverso
REPO_NAME = "simud"                   # Repository di destinazione

def scarica_lista():
    """Scarica la lista IPTV e la divide in eventi italiani e stranieri"""
    try:
        response = requests.get(IPTV_URL)
        response.raise_for_status()
        righe = response.text.splitlines()
        print(f"Righe totali scaricate: {len(righe)}")
        print(f"Prime 5 righe del file:\n{' '.join(righe[:5])}")
    except requests.RequestException as e:
        print(f"Errore durante il download della lista IPTV: {e}")
        return None, None

    eventi_italiani = []
    eventi_stranieri = []

    for i in range(len(righe)):
        if "#EXTINF" in righe[i]:
            evento = righe[i] + "\n" + righe[i + 1] if i + 1 < len(righe) else righe[i]
            print(f"Analizzando evento: {evento.strip()}")
            if any(keyword.lower() in evento.lower() for keyword in PAROLE_CHIAVE_ITALIANE):
                print(f"-> Italiano: {evento.strip()}")
                eventi_italiani.append(evento)
            else:
                print(f"-> Straniero: {evento.strip()}")
                eventi_stranieri.append(evento)

    intestazione = "#EXTM3U\n"
    contenuto_italiano = intestazione + "\n".join(eventi_italiani)
    contenuto_straniero = intestazione + "\n".join(eventi_stranieri)

    print(f"Eventi italiani trovati: {len(eventi_italiani)}")
    print(f"Eventi stranieri trovati: {len(eventi_stranieri)}")
    print(f"Contenuto italiano (prime 500 caratteri):\n{contenuto_italiano[:500]}")
    print(f"Contenuto stran
