import requests
import re
import os

# URL del file m3u8
url = "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/daddylive-events.m3u8"

# URL dell'immagine
logo_url = "https://i.postimg.cc/4y3wNDMQ/Picsart-25-04-12-19-08-51-665.png"

# Percorso del file di output
output_file = "itaevents3.m3u8"

# Pattern per cercare parole legate all'Italia
italy_pattern = re.compile(r'\b(?:IT|ITALY|ITALIA|italia|italy|It|Italy|Italia)\b', re.IGNORECASE)

# Dizionario di traduzioni per i group-title
group_translations = {
    "SOCCER": "Calcio",
    "FOOTBALL": "Calcio",
    "SPORTS": "Sport",
    "SPORT": "Sport",
    "BASKETBALL": "Pallacanestro",
    "TENNIS": "Tennis",
    "MOTORSPORT": "Motorsport",
    "RACING": "Corse",
    "BOXING": "Pugilato",
    "MMA": "Arti Marziali Miste",
    "CRICKET": "Cricket",
    "RUGBY": "Rugby",
    "HOCKEY": "Hockey",
    "GOLF": "Golf",
    "ENTERTAINMENT": "Intrattenimento",
    "NEWS": "Notizie",
    "MOVIES": "Film",
    "MUSIC": "Musica",
    "KIDS": "Bambini",
    "DOCUMENTARY": "Documentari",
    "GENERAL": "Generale",
}

def download_m3u8(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text.splitlines()
    except requests.RequestException as e:
        print(f"Errore nel scaricare il file m3u8: {e}")
        return []

def translate_group_title(group_title):
    return group_translations.get(group_title.upper(), group_title)

def filter_italian_channels(lines):
    filtered_lines = ["#EXTM3U"]
    current_channel = []
    channel_name = None
    
    for line in lines:
        if line.startswith("#EXTINF"):
            current_channel = [line]
            channel_name = line.split(",")[-1].strip()
        elif line.startswith("#") or line.strip() == "":
            if current_channel:
                current_channel.append(line)
        elif line.startswith("http") and current_channel and channel_name:
            if italy_pattern.search(channel_name):
                extinf_line = current_channel[0]
                if 'tvg-logo="' not in extinf_line:
                    extinf_line = extinf_line.replace('tvg-name="', f'tvg-logo="{logo_url}" tvg-name="') if 'tvg-name="' in extinf_line else extinf_line[:-len(channel_name)] + f'tvg-logo="{logo_url}",{channel_name}'
                else:
                    extinf_line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logo_url}"', extinf_line)
                
                if 'group-title="' in extinf_line:
                    current_group = re.search(r'group-title="([^"]*)"', extinf_line)
                    if current_group:
                        group_name = current_group.group(1)
                        translated_group = translate_group_title(group_name)
                        extinf_line = re.sub(r'group-title="[^"]*"', f'group-title="{translated_group}"', extinf_line)
                
                filtered_lines.append(extinf_line)
                filtered_lines.extend(current_channel[1:])
                filtered_lines.append(line)
            current_channel = []
            channel_name = None
    
    return filtered_lines

def save_m3u8(lines, output_path):
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + "\n")
        print(f"File salvato con successo: {output_path}")
    except Exception as e:
        print(f"Errore nel salvare il file: {e}")

def main():
    lines = download_m3u8(url)
    if not lines:
        print("Impossibile procedere, nessun dato scaricato.")
        return
    
    filtered_lines = filter_italian_channels(lines)
    
    if len(filtered_lines) > 1:
        save_m3u8(filtered_lines, output_file)
    else:
        print("Nessun canale italiano trovato.")

if __name__ == "__main__":
    main()
