import requests
import re

# URL del file M3U8
input_url = "https://raw.githubusercontent.com/ciccioxm3/omg/72596e5e7142f99b2a70191101f8983ece1e92f9/onlyevents.m3u8"
# Prefisso da aggiungere ai flussi
prefix = "https://nzo66-tvproxy.hf.space/proxy/m3u?url="

# Scarica il file M3U8
response = requests.get(input_url)
if response.status_code != 200:
    print("Errore nel download del file M3U8")
    exit()

# Leggi il contenuto
lines = response.text.splitlines()

# Lista per il nuovo contenuto
new_lines = []
in_channel = False
current_channel = []

for line in lines:
    if line.startswith("#EXTINF"):
        # Inizio di un nuovo canale
        if current_channel:
            new_lines.extend(current_channel)
        current_channel = [line]
        in_channel = True
    elif in_channel and line.startswith("http"):
        # Modifica il flusso video
        modified_url = prefix + line
        current_channel.append(modified_url)
        in_channel = False
    else:
        if current_channel:
            current_channel.append(line)
        else:
            new_lines.append(line)

# Aggiungi l'ultimo canale
if current_channel:
    new_lines.extend(current_channel)

# Salva il nuovo file M3U8
output_file = "itaevents3.m3u8"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines))

print(f"File modificato salvato come {output_file}")
