import requests
import base64
from github import Github

# Configura il repository e il token
GITHUB_TOKEN = "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"
GITHUB_REPO = "pigzillaaaaa/iptv-scraper"
FILE_PATH_ITALIA = "eventi_italiani.m3u8"
FILE_PATH_STRANIERI = "eventi_stranieri.m3u8"

# URL della playlist IPTV
playlist_url = 'https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/main/daddylive-events.m3u8'

# Parole chiave per eventi italiani
parole_chiave_italiane = [
    'italy', 'serie a', 'serie b', 'italia', 'coppa italia',
    'lega pro', 'nazionale italiana', 'juventus', 'inter',
    'milan', 'napoli', 'roma', 'lazio'
]

def scarica_playlist(url):
    """Scarica la playlist M3U8"""
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def filtra_eventi(contenuto_playlist, parole_chiave):
    """Filtra gli eventi in base alle parole chiave"""
    eventi_filtrati = []
    eventi = contenuto_playlist.split('#EXTINF')
    for evento in eventi:
        if any(parola.lower() in evento.lower() for parola in parole_chiave):
            eventi_filtrati.append('#EXTINF' + evento.strip())
    return '\n'.join(eventi_filtrati)

def aggiorna_file_github(file_path, contenuto):
    """Aggiorna un file nella repository GitHub"""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    
    try:
        file = repo.get_contents(file_path)
        repo.update_file(file.path, f"Aggiornamento {file_path}", contenuto, file.sha)
        print(f"✅ {file_path} aggiornato su GitHub!")
    except:
        repo.create_file(file_path, f"Creazione {file_path}", contenuto)
        print(f"✅ {file_path} creato su GitHub!")

# Scarica la playlist
contenuto_playlist = scarica_playlist(playlist_url)

# Filtra eventi
eventi_italiani = filtra_eventi(contenuto_playlist, parole_chiave_italiane)
eventi_stranieri = filtra_eventi(contenuto_playlist, parole_chiave_italiane)

# Aggiorna i file su GitHub
aggiorna_file_github(FILE_PATH_ITALIA, eventi_italiani)
aggiorna_file_github(FILE_PATH_STRANIERI, eventi_stranieri)
