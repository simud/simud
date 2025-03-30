import requests
import os
from urllib.parse import urlparse

# Squadre italiane di esempio (Serie A, B, C)
serie_a = ["Juventus", "Inter", "Milan", "Napoli", "Roma", "Lazio", "Atalanta", "Fiorentina"]
serie_b = ["Parma", "Brescia", "Cremonese", "Pisa", "Frosinone", "Reggina", "Benevento", "Cosenza"]
serie_c = ["Catanzaro", "Padova", "Vicenza", "Triestina", "Alessandria", "Pro Vercelli", "Carrarese", "Lucchese"]

italian_teams = serie_a + serie_b + serie_c

# URL di esempio da cui prendere i dati (sostituibile con un input dinamico)
GITHUB_URL = os.getenv("GITHUB_URL", "https://raw.githubusercontent.com/randomuser/repo/main/events.txt")

# Funzione per scaricare il contenuto dall'URL
def download_events(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.splitlines()
    else:
        print(f"Errore nel scaricare {url}: {response.status_code}")
        return []

# Funzione per determinare se un evento è italiano
def is_italian_event(line):
    return any(team in line for team in italian_teams)

# Filtra gli eventi e scrive nei file M3U8
def filter_and_write_events(events):
    italian_events = ["#EXTM3U"]
    foreign_events = ["#EXTM3U"]
    
    for line in events:
        if line.startswith("#EXTM3U"):
            continue
        if is_italian_event(line):
            italian_events.append(line)
        else:
            foreign_events.append(line)
    
    with open("eventi_italiani.m3u8", "w") as f:
        f.write("\n".join(italian_events))
    with open("eventi_stranieri.m3u8", "w") as f:
        f.write("\n".join(foreign_events))

# Main
if __name__ == "__main__":
    events = download_events(GITHUB_URL)
    if events:
        filter_and_write_events(events)
        print("File M3U8 generati con successo.")
    else:
        print("Nessun evento trovato.")
