import requests
from github import Github
import os

IPTV_URL = "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/main/daddylive-events.m3u8"
PAROLE_CHIAVE_ITALIANE = [
    "italy", "italia", "serie a", "serie b", "coppa italia", "juventus", "inter", "milan",
    "napoli", "roma", "lazio", "fiorentina", "atalanta", "torino", "bologna", "lecce"
]
FILE_ITALIANO = "eventi_italiani.m3u8"
FILE_STRANIERO = "eventi_stranieri.m3u8"

GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO_OWNER = "<Simud>"  # Sostituisci con il tuo username reale
REPO_NAME = "simud"

def scarica_lista():
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
    print(f"Contenuto italiano (primi 500 caratteri):\n{contenuto_italiano[:500]}")
    print(f"Contenuto straniero (primi 500 caratteri):\n{contenuto_straniero[:500]}")

    return contenuto_italiano, contenuto_straniero

def aggiorna_repo(contenuto_italiano, contenuto_straniero):
    if not GITHUB_TOKEN:
        print("Errore: Token GitHub non trovato!")
        return

    print(f"Token GitHub: {'<presente>' if GITHUB_TOKEN else '<non presente>'}")
    print(f"Tentativo di accesso al repository: {REPO_OWNER}/{REPO_NAME}")

    try:
        g = Github(GITHUB_TOKEN)
        print("Autenticazione con GitHub riuscita")
        repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
        print(f"Repository trovato: {repo.full_name}")

        try:
            file_italiano = repo.get_contents(FILE_ITALIANO)
            repo.update_file(
                file_italiano.path,
                "Aggiornamento eventi italiani",
                contenuto_italiano,
                file_italiano.sha
            )
            print(f"File {FILE_ITALIANO} aggiornato con successo!")
        except:
            repo.create_file(
                FILE_ITALIANO,
                "Creazione eventi italiani",
                contenuto_italiano
            )
            print(f"File {FILE_ITALIANO} creato con successo!")

        try:
            file_straniero = repo.get_contents(FILE_STRANIERO)
            repo.update_file(
                file_straniero.path,
                "Aggiornamento eventi stranieri",
                contenuto_straniero,
                file_straniero.sha
            )
            print(f"File {FILE_STRANIERO} aggiornato con successo!")
        except:
            repo.create_file(
                FILE_STRANIERO,
                "Creazione eventi stranieri",
                contenuto_straniero
            )
            print(f"File {FILE_STRANIERO} creato con successo!")

        print("✅ File aggiornati con successo nel repository simud!")

    except Exception as e:
        print(f"Errore durante l'aggiornamento del repository: {e}")

if __name__ == "__main__":
    eventi_ita, eventi_str = scarica_lista()
    if eventi_ita is not None and eventi_str is not None:
        aggiorna_repo(eventi_ita, eventi_str)
    else:
        print("Errore: impossibile procedere con l'aggiornamento a causa di un problema nel download.")
