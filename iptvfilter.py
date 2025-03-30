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
GITHUB_REPO = "pigzillaaaaa/iptv-scraper"  # Nome della tua repo


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


def aggiorna_repo(contenuto_italiano, contenuto_straniero):
    """Aggiorna i file nella repository GitHub"""
    if not GITHUB_TOKEN:
        print("Errore: Token GitHub non trovato!")
        return

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        # Lista dei file da aggiornare
        file_dict = {
            FILE_ITALIANO: contenuto_italiano,
            FILE_STRANIERO: contenuto_straniero
        }

        for file_name, contenuto in file_dict.items():
            try:
                file = repo.get_contents(file_name)
                repo.update_file(file.path, f"Aggiornamento automatico {file_name}", contenuto, file.sha)
            except Exception:
                repo.create_file(file_name, f"Creazione file {file_name}", contenuto)

        print("✅ Liste IPTV aggiornate con successo su GitHub!")
    except Exception as e:
        print(f"Errore durante l'aggiornamento su GitHub: {e}")


if __name__ == "__main__":
    eventi_ita, eventi_str = scarica_lista()
    if eventi_ita is not None and eventi_str is not None:
        aggiorna_repo(eventi_ita, eventi_str)
