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
            evento = righe[i] + "\n" + righe[i + 1] if i + 1 < len(righe) else righe[i]
            if any(keyword.lower() in evento.lower() for keyword in PAROLE_CHIAVE_ITALIANE):
                eventi_italiani.append(evento)
            else:
                eventi_stranieri.append(evento)

    # Aggiungi l'intestazione M3U8 ai file
    intestazione = "#EXTM3U\n"
    return intestazione + "\n".join(eventi_italiani), intestazione + "\n".join(eventi_stranieri)

def aggiorna_repo(contenuto_italiano, contenuto_straniero):
    """Aggiorna i file nel repository GitHub usando PyGithub"""
    if not GITHUB_TOKEN:
        print("Errore: Token GitHub non trovato!")
        return

    try:
        # Inizializza il client GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")

        # Aggiorna o crea il file italiano
        try:
            file_italiano = repo.get_contents(FILE_ITALIANO)
            repo.update_file(
                file_italiano.path,
                "Aggiornamento eventi italiani",
                contenuto_italiano,
                file_italiano.sha
            )
        except:
            repo.create_file(
                FILE_ITALIANO,
                "Creazione eventi italiani",
                contenuto_italiano
            )

        # Aggiorna o crea il file straniero
        try:
            file_straniero = repo.get_contents(FILE_STRANIERO)
            repo.update_file(
                file_straniero.path,
                "Aggiornamento eventi stranieri",
                contenuto_straniero,
                file_straniero.sha
            )
        except:
            repo.create_file(
                FILE_STRANIERO,
                "Creazione eventi stranieri",
                contenuto_straniero
            )

        print("✅ File aggiornati con successo nel repository!")

    except Exception as e:
        print(f"Errore durante l'aggiornamento del repository: {e}")

if __name__ == "__main__":
    eventi_ita, eventi_str = scarica_lista()
    if eventi_ita is not None and eventi_str is not None:
        aggiorna_repo(eventi_ita, eventi_str)
