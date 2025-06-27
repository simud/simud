import requests
import re
import os
from github import Github
from github import GithubException

# URL della playlist
url = "https://nzo66-tvproxy.hf.space/proxy?url=https://raw.githubusercontent.com/nzo66/TV/refs/heads/main/lista.m3u"

# Gruppi desiderati
gruppi_desiderati = ["Bambini", "Sport", "Film & Serie TV", "Documentari", "Eventi Live"]

# Canali da escludere (solo per Film & Serie TV)
canali_esclusi = [
    "CRIME + INV", "CRIME+ INVESTIGATION", "FOX", "PREMIUM CRIME",
    "RAKUTEN ACTION MOVIES", "RAKUTEN COMEDY MOVIES", "RAKUTEN DRAMA",
    "RAKUTEN FAMILY", "RAKUTEN TOP FREE", "RAKUTEN TV SHOWS", "TOP CRIME"
]

# Canali Sky Primafila da rinominare e ordinare
sky_primafila_names = [
    "SKY PRIMAFILA 1", "SKY PRIMAFILA 1 (2)", "SKY PRIMAFILA 2", "SKY PRIMAFILA 2 (2)",
    "SKY PRIMAFILA 3", "SKY PRIMAFILA 3 (2)", "SKY PRIMAFILA 4", "SKY PRIMAFILA 4 (2)",
    "SKY PRIMAFILA 5", "SKY PRIMAFILA 5 (2)", "SKY PRIMAFILA 6", "SKY PRIMAFILA 6 (2)",
    "SKY PRIMAFILA 7", "SKY PRIMAFILA 7 (2)", "SKY PRIMAFILA 8", "SKY PRIMAFILA 8 (2)",
    "SKY PRIMAFILA 9", "SKY PRIMAFILA 9 (2)", "SKY PRIMAFILA 10", "SKY PRIMAFILA 10 (2)",
    "SKY PRIMAFILA 12", "SKY PRIMAFILA 14", "SKY PRIMAFILA 15", "SKY PRIMAFILA 16",
    "SKY PRIMAFILA 17", "SKY PRIMAFILA 18"
]

# Canali da rinominare in Sky Uno FHD e spostare in Intrattenimento
sky_uno_names = ["SKY SPORT UNO", "SKY SPORT UNO (2)"]

# Canale da rinominare in Sky Serie FHD e spostare in Intrattenimento
sky_serie_names = ["SKY SERIE"]

# Logo per i canali Eventi Live (ora Eventi Sportivi) senza logo
eventi_logo = "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-uno-it.png"

# Loghi per i gruppi (non utilizzato per mantenere i loghi originali tranne per Eventi Sportivi)
logos = {
    "Sky Sport FHD Backup": "https://i.postimg.cc/5063BN23/photo-2025-03-12-12-27-02.png",
    "Intrattenimento": "https://i.postimg.cc/NFGs2Ptq/photo-2025-03-12-12-36-48.png",
    "Sky Cinema FHD Backup": "https://i.postimg.cc/Ss88rXcm/photo-2025-03-12-12-23-14.png",
    "Sky Primafila FHD": "https://i.postimg.cc/VL0pBWFX/Picsart-25-04-16-23-24-42-819.png"
}

# Percorso del file di output nella directory di lavoro corrente
output_file = "./vavoofunzionante.m3u8"

# Configurazione per GitHub
GITHUB_TOKEN = os.getenv("GH_TOKEN")  # Token di accesso personale GitHub
REPO_NAME = "nome-utente/vavoo-playlist"  # Sostituisci con il tuo nome-utente/nome-repository
FILE_PATH = "vavoofunzionante.m3u8"  # Percorso del file nel repository

# Canale ADMIN da aggiungere alla fine del gruppo Eventi Sportivi
canale_admin = [
    '#EXTINF:-1 tvg-id="ADMIN" tvg-name="ADMIN" tvg-logo="https://i.postimg.cc/4ysKkc1G/photo-2025-03-28-15-49-45.png" group-title="Eventi Sportivi",ADMIN',
    'https://static.vecteezy.com/system/resources/previews/033/861/932/mp4/gherkins-close-up-loop-free-video.mp4'
]

# Funzione per convertire il nome in formato con solo la prima lettera maiuscola
def title_case_name(name):
    # Rimuove "(2)" e altri suffissi simili
    name = re.sub(r'\s*\(2\)', '', name)
    # Converte in minuscolo e poi capitalizza ogni parola
    return ' '.join(word.capitalize() for word in name.lower().split())

# Scarica la playlist
response = requests.get(url)
if response.status_code != 200:
    print("Errore nel scaricare la playlist")
    exit()

# Inizializza la nuova playlist con l'intestazione
new_playlist = ["#EXTM3U"]
sky_primafila_channels = []  # Lista temporanea per i canali Sky Primafila
eventi_sportivi_channels = []  # Lista temporanea per i canali Eventi Sportivi

# Set per raccogliere i nomi dei gruppi trovati (per debug)
gruppi_trovati = set()

# Variabile per tenere traccia del gruppo corrente
current_group = None
lines = response.text.splitlines()

# Analizza le righe della playlist
for i, line in enumerate(lines):
    # Cerca le righe con group-title
    group_match = re.search(r'group-title="([^"]+)"', line)
    if group_match:
        current_group = group_match.group(1)
        # Aggiungi il gruppo trovato al set per debug
        gruppi_trovati.add(current_group)
        # Verifica se il gruppo è tra quelli desiderati
        if current_group in gruppi_desiderati:
            # Cerca il tvg-name
            tvg_name_match = re.search(r'tvg-name="([^"]+)"', line)
            if tvg_name_match:
                tvg_name = tvg_name_match.group(1)
                # Escludi i canali indesiderati solo per Film & Serie TV
                if current_group != "Film & Serie TV" or tvg_name not in canali_esclusi:
                    # Rimuovi "(2)" da tvg-name
                    new_tvg_name = re.sub(r'\s*\(2\)', '', tvg_name)
                    # Converti il nome in formato con prima lettera maiuscola
                    display_name = title_case_name(new_tvg_name)
                    # Aggiungi "FHD" solo se non è Eventi Live
                    if current_group != "Eventi Live":
                        display_name += " FHD"
                    
                    # Determina il nuovo group-title
                    new_group_title = current_group
                    if tvg_name in sky_uno_names or tvg_name in sky_serie_names:
                        new_group_title = "Sky Sport FHD Backup"
                    elif tvg_name in sky_primafila_names:
                        new_group_title = "Sky Primafila FHD"
                    elif current_group == "Film & Serie TV":
                        new_group_title = "Sky Cinema FHD Backup"
                    elif current_group == "Sport":
                        new_group_title = "Sky Sport FHD Backup"
                    elif current_group == "Eventi Live":
                        new_group_title = "Eventi Sportivi"
                    
                    # Modifica la riga
                    modified_line = re.sub(r'tvg-name="[^"]+"', f'tvg-name="{display_name}"', line)
                    modified_line = re.sub(r'group-title="[^"]+"', f'group-title="{new_group_title}"', modified_line)
                    modified_line = re.sub(r',[^,]+$', f',{display_name}', modified_line)
                    
                    # Aggiungi il logo per i canali Eventi Sportivi senza logo
                    if current_group == "Eventi Live" and not re.search(r'tvg-logo="[^"]+"', modified_line):
                        modified_line = re.sub(r'(#EXTINF:[^,]+),', f'\\1 tvg-logo="{eventi_logo}",', modified_line)
                    
                    # Gestisci i canali Sky Uno
                    if tvg_name in sky_uno_names:
                        modified_line = re.sub(r'tvg-name="[^"]+"', 'tvg-name="Sky Sport Uno FHD"', modified_line)
                        modified_line = re.sub(r',[^,]+$', ',Sky Sport Uno FHD', modified_line)
                        new_playlist.append(modified_line)
                        if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                            new_playlist.append(lines[i + 1])
                    # Gestisci il canale Sky Serie
                    elif tvg_name in sky_serie_names:
                        modified_line = re.sub(r'tvg-name="[^"]+"', 'tvg-name="Sky Serie FHD"', modified_line)
                        modified_line = re.sub(r',[^,]+$', ',Sky Serie FHD', modified_line)
                        new_playlist.append(modified_line)
                        if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                            new_playlist.append(lines[i + 1])
                    # Gestisci i canali Sky Primafila
                    elif tvg_name in sky_primafila_names:
                        sky_primafila_channels.append((modified_line, lines[i + 1] if i + 1 < len(lines) and not lines[i + 1].startswith("#") else ""))
                    # Gestisci i canali Eventi Sportivi
                    elif current_group == "Eventi Live":
                        eventi_sportivi_channels.append((modified_line, lines[i + 1] if i + 1 < len(lines) and not lines[i + 1].startswith("#") else ""))
                    else:
                        # Aggiungi direttamente alla playlist
                        new_playlist.append(modified_line)
                        if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                            new_playlist.append(lines[i + 1])

# Funzione per estrarre il numero da tvg-name di Sky Primafila
def get_primafila_number(tvg_name):
    match = re.search(r'Sky Primafila (\d+)', tvg_name)
    return int(match.group(1)) if match else float('inf')

# Filtra e ordina i canali Sky Primafila
valid_sky_primafila_channels = []
for channel in sky_primafila_channels:
    tvg_name_match = re.search(r'tvg-name="([^"]+)"', channel[0])
    if not tvg_name_match:
        print(f"Errore: tvg-name non trovato nella riga: {channel[0]}")
        continue
    tvg_name = tvg_name_match.group(1)
    if tvg_name not in [title_case_name(name) + " FHD" for name in [re.sub(r'\s*\(2\)', '', n) for n in sky_primafila_names]]:
        print(f"Errore: tvg-name non valido per Sky Primafila: {tvg_name}")
        continue
    valid_sky_primafila_channels.append(channel)

# Ordina i canali Sky Primafila per numero
valid_sky_primafila_channels.sort(key=lambda x: get_primafila_number(re.search(r'tvg-name="([^"]+)"', x[0]).group(1)))

# Aggiungi i canali Sky Primafila ordinati alla playlist
for extinf, url in valid_sky_primafila_channels:
    new_playlist.append(extinf)
    if url:
        new_playlist.append(url)

# Aggiungi i canali Eventi Sportivi alla playlist
for extinf, url in eventi_sportivi_channels:
    new_playlist.append(extinf)
    if url:
        new_playlist.append(url)

# Aggiungi esplicitamente il canale ADMIN alla fine del gruppo Eventi Sportivi
new_playlist.extend(canale_admin)

# Scrivi la nuova playlist nella directory di lavoro corrente
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(new_playlist))

# Carica il file su GitHub
if GITHUB_TOKEN:
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        # Cerca se il file esiste già
        try:
            file = repo.get_contents(FILE_PATH)
            # Aggiorna il file esistente
            repo.update_file(
                path=FILE_PATH,
                message="Aggiornamento automatico della playlist vavoofunzionante.m3u8",
                content=content,
                sha=file.sha
            )
            print(f"File {FILE_PATH} aggiornato con successo su GitHub")
        except:
            # Crea un nuovo file
            repo.create_file(
                path=FILE_PATH,
                message="Creazione iniziale della playlist vavoofunzionante.m3u8",
                content=content
            )
            print(f"File {FILE_PATH} creato con successo su GitHub")
    except GithubException as e:
        print(f"Errore durante il caricamento su GitHub: {e}")
else:
    print("GITHUB_TOKEN non trovato. Il file non è stato caricato su GitHub.")

# Stampa i gruppi trovati per debug
print("Gruppi trovati nella playlist:", sorted(gruppi_trovati))
print(f"Playlist creata con successo: {output_file}")
