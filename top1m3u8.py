import os

# Percorso del file di output sul desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "top1.m3u8")
base_url = "https://calcionew.newkso.ru/calcio/"
logo_url = "https://i.postimg.cc/NFGs2Ptq/photo-2025-03-12-12-36-48.png"

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
        "serie1": "Serie A 1", "seriesi": "Sky Serie", "sky258": "Sky 258", "sky259": "Sky 259",
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
    m3u8_content += f'#EXTINF:-1 tvg-id="{channel_name}" tvg-name="{channel_name}" tvg-logo="https://i.postimg.cc/NFGs2Ptq/photo-2025-03-12-12-36-48.png" group-title="Italy HD",{channel_name}\n'
    m3u8_content += f"{channel_url}\n\n"

# Aggiungi il canale finale
m3u8_content += f'#EXTINF:-1 tvg-id="ADMIN" tvg-name="ADMIN" tvg-logo="https://i.postimg.cc/NFGs2Ptq/photo-2025-03-12-12-36-48.png" group-title="Italy HD",ADMIN\n'
m3u8_content += "https://static.vecteezy.com/system/resources/previews/033/861/932/mp4/gherkins-close-up-loop-free-video.mp4\n"

# Salva il file sul desktop
try:
    with open(desktop_path, "w", encoding="utf-8") as f:
        f.write(m3u8_content)
    print(f"Playlist salvata con successo in: {desktop_path}")
except Exception as e:
    print(f"Errore durante il salvataggio del file: {e}")
