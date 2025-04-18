import requests
import re
import os
from github import Github
from github import GithubException

# URL della playlist
url = "https://raw.githubusercontent.com/realbestia/itatv/e93adee56379c15ee37c4cd54c8a1f1fc0cecfac/combined_playlist.m3u8"

# Gruppi desiderati
gruppi_desiderati = ["Bambini", "Sport", "Film & Serie TV", "Documentari"]

# Canali da escludere (tvg-name)
canali_esclusi = [
    # Canali Sport esclusi
    "ACI SPORT TV", "DAZN2", "RTV SAN MARINO SPORT", "RTV SPORT", "SKY SPORT",
    "SKY SPORT 24", "SKY SPORT 24 [LIVE DURING EVENTS ONLY]", "SKY SPORT ARENA",
    "SKY SPORT F1", "SKY SPORT FOOTBALL [LIVE DURING EVENTS ONLY]", "SKY SPORT GOLF",
    "SKY SPORT MAX", "SKY SPORT MOTO GP", "SKY SPORT MOTOGP", "SKY SPORT NBA",
    "SKY SPORT SERIE A", "SKY SPORT TENNIS", "SKY SPORTS F1", "SKY SUPER TENNIS",
    "SPORT ITALIA", "SPORT ITALIA SOLO CALCIO [LIVE DURING EVENTS ONLY]",
    "SPORTITALIA PLUS", "SPORTITALIA SOLOCALCIO", "SUPER TENNIS", "TENNIS CHANNEL",
    "TOP CALCIO 24", "TRSPORT",
    # Canali Film & Serie TV esclusi
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

# Loghi per i gruppi
logos = {
    "DAZN Serie A ": "https://i.postimg.cc/5063BN23/photo-2025-03-12-12-27-02.png",
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

# Scarica la playlist
response = requests.get(url)
if response.status_code != 200:
    print("Errore nel scaricare la playlist")
    exit()

# Inizializza la nuova playlist con l'intestazione
new_playlist = ["#EXTM3U"]
sky_primafila_channels = []  # Lista temporanea per i canali Sky Primafila

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
                # Escludi i canali indesiderati
                if tvg_name not in canali_esclusi:
                    # Rimuovi "(2)" da tvg-name e dal nome visualizzato
                    new_tvg_name = re.sub(r'\s*\(2\)', '', tvg_name)
                    modified_line = re.sub(r'tvg-name="[^"]+"', f'tvg-name="{new_tvg_name}"', line)
                    modified_line = re.sub(r',[^,]+$', f',{new_tvg_name}', modified_line)
                    
                    # Determina il nuovo group-title
                    new_group_title = current_group
                    if tvg_name in sky_uno_names or tvg_name in sky_serie_names:
                        new_group_title = "Intrattenimento"
                        modified_line = re.sub(r'group-title="[^"]+"', f'group-title="{new_group_title}"', modified_line)
                    elif tvg_name in sky_primafila_names:
                        new_group_title = "Sky Primafila FHD"
                        modified_line = re.sub(r'group-title="Film & Serie TV"', f'group-title="{new_group_title}"', modified_line)
                    elif current_group == "Film & Serie TV":
                        new_group_title = "Sky Cinema FHD Backup"
                        modified_line = re.sub(r'group-title="Film & Serie TV"', f'group-title="{new_group_title}"', modified_line)
                    elif current_group == "Sport":
                        new_group_title = "DAZN Serie A "
                        modified_line = re.sub(r'group-title="Sport"', f'group-title="{new_group_title}"', modified_line)
                    
                    # Assegna il logo in base al nuovo group-title
                    if new_group_title in logos:
                        modified_line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logos[new_group_title]}"', modified_line)
                    
                    # Gestisci i canali Sky Uno
                    if tvg_name in sky_uno_names:
                        modified_line = re.sub(r'tvg-name="[^"]+"', 'tvg-name="Sky Uno FHD"', modified_line)
                        modified_line = re.sub(r',[^,]+$', ',Sky Uno FHD', modified_line)
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
                    else:
                        # Aggiungi direttamente alla playlist
                        new_playlist.append(modified_line)
                        if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                            new_playlist.append(lines[i + 1])

# Funzione per estrarre il numero da tvg-name di Sky Primafila
def get_primafila_number(tvg_name):
    match = re.search(r'SKY PRIMAFILA (\d+)', tvg_name)
    return int(match.group(1)) if match else float('inf')

# Filtra e ordina i canali Sky Primafila
valid_sky_primafila_channels = []
for channel in sky_primafila_channels:
    tvg_name_match = re.search(r'tvg-name="([^"]+)"', channel[0])
    if not tvg_name_match:
        print(f"Errore: tvg-name non trovato nella riga: {channel[0]}")
        continue
    tvg_name = tvg_name_match.group(1)
    if tvg_name not in [re.sub(r'\s*\(2\)', '', name) for name in sky_primafila_names]:
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
