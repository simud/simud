import requests
import re

# URL del file M3U8
input_url = "https://raw.githubusercontent.com/ciccioxm3/omg/72596e5e7142f99b2a70191101f8983ece1e92f9/onlyevents.m3u8"
# Prefisso da aggiungere ai flussi
prefix = "https://nzo66-tvproxy.hf.space/proxy/m3u?url="

# Scarica il file M3U8
try:
    response = requests.get(input_url)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"Errore nel download del file M3U8: {e}")
    exit()

# Leggi il contenuto
lines = response.text.splitlines()

# Lista per il nuovo contenuto
new_lines = []
current_channel = []
is_channel = False

for line in lines:
    if line.startswith("#EXTINF"):
        # Inizio di un nuovo canale
        if current_channel:
            new_lines.extend(current_channel)
        current_channel = [line]
        is_channel = True
    elif is_channel and line.strip() and line.startswith("http"):
        # Modifica l'URL del flusso
        modified_url = prefix + line
        # Modifica il nome del canale nella riga EXTINF
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
        # Scrivi il canale completo e resetta
        new_lines.extend(current_channel)
        current_channel = []
        is_channel = False
    elif is_channel and line.strip():
        # Aggiungi righe intermedie (es. #EXTVLCOPT)
        current_channel.append(line)
    else:
        # Righe fuori da un canale (es. #EXTM3U)
        if current_channel:
            new_lines.extend(current_channel)
            current_channel = []
            is_channel = False
        new_lines.append(line)

# Aggiungi l'ultimo canale, se presente
if current_channel:
    new_lines.extend(current_channel)

# Salva il nuovo file M3U8
output_file = "itaevents3.m3u8"
try:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    print(f"File modificato salvato come {output_file}")
except Exception as e:
    print(f"Errore nel salvataggio del file: {e}")
