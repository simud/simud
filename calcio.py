import os
import sys
from dotenv import load_dotenv

# Determina il percorso della directory dello script
script_dir = os.path.dirname(__file__)

# Carica le variabili d'ambiente dal file .env nella directory dello script
dotenv_path = os.path.join(script_dir, ".env")
load_dotenv(dotenv_path=dotenv_path)

# Determina il percorso di output
# Salva il file M3U nella directory di lavoro corrente (dove lo script viene eseguito)
output_path = os.path.join(os.getcwd(), "calcio_playlist.m3u8")

# Non sono più necessarie MFP e PSW, poiché non usiamo il proxy
# MFP = os.getenv("MFP")
# PSW = os.getenv("PSW")

base_url = "https://calcionew.newkso.ru/calcio/"
logo_url = "https://www.igizmo.it/wp-content/uploads/2024/05/skystream-3.jpg"

# Lista dei canali fornita
channels_raw = [
    "Bari/", "Dazn1/", "brescia/", "bundes/", "calcioX1ac/", "calcioX1comedycentral/",
    "calcioX1eurosport1/", "calcioX1eurosport2/", "calcioX1formula1/", "calcioX1history/",
    "calcioX1seriesi/", "calcioX1sky258/", "calcioX1sky259/", "calcioX1skyatlantic/",
    "calcioX1skycinemacollection/", "calcioX1skycinemacomedy/", "calcioX1skycinemadrama/",
    "calcioX1skycinemadue/", "calcioX1skycinemafamily/", "calcioX1skycinemaromance/",
    "calcioX1skycinemasuspence/", "calcioX1skycinemauno/", "calcioX1skycrime/",
    "calcioX1skydocumentaries/", "calcioX1skyinvestigation/", "calcioX1skynature/",
    "calcioX1skyserie/", "calcioX1skysport24/", "calcioX1skysport251/",
    "calcioX1skysport252/", "calcioX1skysport253/", "calcioX1skysport254/",
    "calcioX1skysport255/", "calcioX1skysport257/", "calcioX1skysportarena/",
    "calcioX1skysportcalcio/", "calcioX1skysportgolf/", "calcioX1skysportmax/",
    "calcioX1skysportmotogp/", "calcioX1skysportnba/", "calcioX1skysporttennis/",
    "calcioX1skysportuno/", "calcioX1skyuno/", "calcioX2ac/", "calcioX2comedycentral/",
    "calcioX2eurosport1/", "calcioX2eurosport2/", "calcioX2formula/", "calcioX2formula1/",
    "calcioX2history/", "calcioX2laliga/", "calcioX2porto/", "calcioX2portugal/",
    "calcioX2serie/", "calcioX2serie1/", "calcioX2seriesi/", "calcioX2sky258/",
    "calcioX2sky259/", "calcioX2skyarte/", "calcioX2skyatlantic/", "calcioX2skycinemacollection/",
    "calcioX2skycinemacomedy/", "calcioX2skycinemadrama/", "calcioX2skycinemadue/",
    "calcioX2skycinemafamily/", "calcioX2skycinemaromance/", "calcioX2skycinemasuspence/",
    "calcioX2skycinemauno/", "calcioX2skycrime/", "calcioX2skydocumentaries/",
    "calcioX2skyinvestigation/", "calcioX2skynature/", "calcioX2skyserie/",
    "calcioX2skysport24/", "calcioX2skysport251/", "calcioX2skysport252/",
    "calcioX2skysport253/", "calcioX2skysport254/", "calcioX2skysport255/",
    "calcioX2skysport256/", "calcioX2skysport257/", "calcioX2skysportarena/",
    "calcioX2skysportcalcio/", "calcioX2skysportgolf/", "calcioX2skysportmax/",
    "calcioX2skysportmotogp/", "calcioX2skysportnba/", "calcioX2skysporttennis/",
    "calcioX2skysportuno/", "calcioX2skyuno/", "calcioX2solocalcio/", "calcioX2sportitalia/",
    "calcioX2zona/", "calcioX2zonab/", "calcioXac/", "calcioXcomedycentral/",
    "calcioXeurosport1/", "calcioXeurosport2/", "calcioXformula1/", "calcioXhistory/",
    "calcioXseriesi/", "calcioXsky258/", "calcioXsky259/", "calcioXskyarte/",
    "calcioXskyatlantic/", "calcioXskycinemacollection/", "calcioXskycinemacomedy/",
    "calcioXskycinemadrama/", "calcioXskycinemadue/", "calcioXskycinemafamily/",
    "calcioXskycinemaromance/", "calcioXskycinemasuspence/", "calcioXskycinemauno/",
    "calcioXskycrime/", "calcioXskydocumentaries/", "calcioXskyinvestigation/",
    "calcioXskynature/", "calcioXskyserie/", "calcioXskysport24/", "calcioXskysport251/",
    "calcioXskysport252/", "calcioXskysport253/", "calcioXskysport254/",
    "calcioXskysport255/", "calcioXskysport256/", "calcioXskysport257/",
    "calcioXskysportarena/", "calcioXskysportcalcio/", "calcioXskysportgolf/",
    "calcioXskysportmax/", "calcioXskysportmotogp/", "calcioXskysportnba/",
    "calcioXskysporttennis/", "calcioXskysportuno/", "calcioXskyuno/", "catan/",
    "cesena/", "juve/", "ligue1/", "pisa/", "saler/", "samp/", "sass/", "spezia/"
]

# Canali extra da aggiungere
extra_channels = [
    ("Inter", "Inter/mono.m3u8"),
    ("Milan", "Milan/mono.m3u8"),
    ("Rai Sport", "RaiSport/mono.m3u8"),
    ("Sky Sport F1", "calcioXskysportf1/mono.m3u8")
]

# Funzione per determinare il group-title basandosi sul nome del canale
def determine_group_title(channel_name):
    """
    Determina il group-title basandosi sul nome del canale secondo le regole specificate:
    1. Se contiene "sport" -> "Sport;Calcio TOP1"
    2. Se contiene parole chiave specifiche -> "Sky;Calcio TOP1"
    3. Default -> "Sport;Calcio TOP1"
    """
    # Parole chiave che identificano canali "Sky;Calcio TOP1"
    sky_keywords = [
        'serie', 'comedy', 'cinema', 'arte', 'atlantic', 'crime',
        'documentaries', 'investigation', 'nature', 'sky uno', 'Sky Uno', 'skyuno'
    ]

    channel_name_lower = channel_name.lower()

    # Controlla se contiene "sport" - priorità massima
    if 'sport' in channel_name_lower:
        return "Sport;Calcio TOP1"

    # Controlla se contiene una delle parole chiave per "Sky;Calcio TOP1"
    for keyword in sky_keywords:
        if keyword.lower() in channel_name_lower:
            return "Sky;Calcio TOP1"

    # Default per tutto il resto
    return "Sport;Calcio TOP1"

# Funzione per pulire e formattare il nome del canale
def format_channel_name(raw_name):
    name = raw_name.rstrip("/")
    # Rimuovi prefissi inutili e normalizza
    for prefix in ["calcioX1", "calcioX2", "calcioX"]:
        if name.startswith(prefix):
            name = name[len(prefix):]
    # Mappa per nomi più leggibili
    name_map = {
        "ac": "Sky Cinema Action",
        "brescia": "Brescia", "bundes": "Bundesliga", "catan": "Catanzaro",
        "cesena": "Cesena", "comedycentral": "Comedy Central", "dazn1": "DAZN 1",
        "eurosport1": "Eurosport 1", "eurosport2": "Eurosport 2", "formula": "Formula 1",
        "formula1": "Formula 1", "history": "History", "juve": "Juventus", "laliga": "LaLiga",
        "ligue1": "Ligue 1", "pisa": "Pisa", "porto": "Porto", "portugal": "Portugal",
        "saler": "Salernitana", "samp": "Sampdoria", "sass": "Sassuolo", "serie": "Serie A",
        "serie1": "SerieA 1", "seriesi": "Sky Serie", "sky258": "Sky 258", "sky259": "Sky 259",
        "skyarte": "Sky Arte", "skyatlantic": "Sky Atlantic", "skycinemacollection": "Sky Cinema Collection",
        "skycinemacomedy": "Sky Cinema Comedy", "skycinemadrama": "Sky Cinema Drama",
        "skycinemadue": "Sky Cinema Due", "skycinemafamily": "Sky Cinema Family",
        "skycinemaromance": "Sky Cinema Romance", "skycinemasuspence": "Sky Cinema Suspense",
        "skycinemauno": "Sky Cinema Uno", "skycrime": "Sky Crime", "skydocumentaries": "Sky Documentaries",
        "skyinvestigation": "Sky Investigation", "skynature": "Sky Nature", "skyserie": "Sky Serie",
        "skysport24": "Sky Sport 24", "skysport251": "Sky Sport 251", "skysport252": "Sky Sport 252",
        "skysport253": "Sky Sport 253", "skysport254": "Sky Sport 254", "skysport255": "Sky Sport 255",
        "skysport256": "Sky Sport 256", "skysport257": "Sky Sport 257", "skysportarena": "Sky Sport Arena",
        "skysportcalcio": "Sky Sport Calcio", "skysportgolf": "Sky Sport Golf", "skysportmax": "Sky Sport Max",
        "skysportmotogp": "Sky Sport MotoGP", "skysportnba": "Sky Sport NBA", "skysporttennis": "Sky Sport Tennis",
        "skysportuno": "Sky Sport Uno", "skyuno": "Sky Uno", "solocalcio": "Solo Calcio",
        "sportitalia": "Sportitalia", "spezia": "Spezia", "zona": "Zona DAZN", "zonab": "Zona B"
    }
    return name_map.get(name.lower(), name.capitalize())

# Crea la lista dei canali
channels = []
for raw_name in channels_raw:
    clean_name = format_channel_name(raw_name)
    # URL diretto senza proxy
    url = f"{base_url}{raw_name}mono.m3u8"
    channels.append((clean_name, url))

# Aggiungi i canali extra
for name, path in extra_channels:
    url = f"{base_url}{path}"
    channels.append((name, url))

# Ordina i canali alfabeticamente
channels.sort(key=lambda x: x[0].lower())

# Crea il contenuto della playlist M3U8
m3u8_content = "#EXTM3U\n\n"
for channel_name, channel_url in channels:
    # Modifica per tvg-id: minuscolo + .it
    tvg_id_formatted = f"{channel_name.lower()}.it"
    # Modifica per il nome visualizzato del canale: aggiungi (CT1)
    display_name_formatted = f"{channel_name} (CT1)"

    # Determina il group-title usando le nuove regole
    group_title = determine_group_title(channel_name)

    # Debug: stampa l'assegnazione per verifica
    print(f"Canale: {channel_name} -> Group-title: {group_title}")

    m3u8_content += f'#EXTINF:-1 tvg-id="{tvg_id_formatted}" tvg-name="{channel_name}" tvg-logo="{logo_url}" group-title="{group_title}",{display_name_formatted}\n'
    m3u8_content += f'#EXTVLCOPT:http-referrer=https://calcionew.newkso.ru\n'
    m3u8_content += f'#EXTVLCOPT:http-origin=https://calcionew.newkso.ru\n'
    m3u8_content += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1\n'
    m3u8_content += f"{channel_url}\n\n"

# Salva il file
try:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(m3u8_content)
    print(f"\nPlaylist salvata con successo in: {output_path}")
    print(f"Totale canali processati: {len(channels)}")
except Exception as e:
    print(f"Errore durante il salvataggio del file: {e}")
    sys.exit(1)
