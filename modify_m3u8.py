import requests
import re

# URL del file M3U8 da scaricare
input_url = "https://raw.githubusercontent.com/ciccioxm3/OMGTV/refs/heads/main/onlyevents.m3u8"
# Prefisso proxy da applicare a ogni flusso
proxy_prefix = "https://mfp2.nzo66.com/extractor/video?host=DLHD&d="
# Suffisso da aggiungere alla fine di ogni flusso
proxy_suffix = "&redirect_stream=true&api_password=mfp123"

# Scarica il file M3U8
try:
    response = requests.get(input_url)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"Errore nel download del file M3U8: {e}")
    exit()

# Leggi le righe del file
lines = response.text.splitlines()

# Nuove righe da scrivere
new_lines = []
current_channel = []
is_channel = False

for line in lines:
    if line.startswith("#EXTINF"):
        # Nuovo canale
        if current_channel:
            new_lines.extend(current_channel)
        current_channel = [line]
        is_channel = True
    elif is_channel and line.strip():
        # Controlla se la riga è un URL (relativo o assoluto)
        if line.startswith("/proxy/m3u?url=") or line.startswith("http"):
            # Estrai l'URL originale
            match = re.search(r'url=(https?://[^&]+)', line)
            if match:
                original_url = match.group(1)
            else:
                # Se non c'è "url=", considera l'intera riga come URL
                original_url = line.replace("/proxy/m3u?url=", "") if line.startswith("/proxy/m3u?url=") else line

            # Applica il nuovo proxy e il suffisso
            modified_url = proxy_prefix + original_url + proxy_suffix

            # Modifica il nome del canale
            extinf_line = current_channel[0]
            tvg_name_match = re.search(r'tvg-name="([^"]+)"', extinf_line)
            if tvg_name_match:
                tvg_name = tvg_name_match.group(1)
                try:
                    original_channel_name = extinf_line.split(",")[-1].strip()
                    new_channel_name = f"{tvg_name} ({original_channel_name})"
                    new_extinf = ",".join(extinf_line.split(",")[:-1] + [new_channel_name])
                    current_channel[0] = new_extinf
                except IndexError:
                    print(f"Errore nella riga EXTINF: {extinf_line}")
            else:
                print(f"tvg-name non trovato in: {extinf_line}")

            # Aggiungi l'URL modificato
            current_channel.append(modified_url)
            # Scrivi blocco canale e resetta
            new_lines.extend(current_channel)
            current_channel = []
            is_channel = False
        else:
            # Altre righe intermedie (#EXTVLCOPT ecc.)
            current_channel.append(line)
    else:
        # Righe fuori dai blocchi canale
        if current_channel:
            new_lines.extend(current_channel)
            current_channel = []
            is_channel = False
        new_lines.append(line)

# Aggiungi eventuale ultimo canale
if current_channel:
    new_lines.extend(current_channel)

# Salva nuovo file M3U8
output_file = "itaevents3.m3u8"
try:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    print(f"File modificato salvato come {output_file}")
except Exception as e:
    print(f"Errore nel salvataggio del file: {e}")
