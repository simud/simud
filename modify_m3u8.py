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

# Variabili per gestire i canali
current_extinf = None
for line in lines:
    if line.startswith("#EXTINF"):
        current_extinf = line
        new_lines.append(line)  # Aggiungi temporaneamente, verrà modificata dopo
    elif current_extinf and line.strip() and line.startswith("http"):
        # Modifica l'URL del flusso
        modified_url = prefix + line
        # Modifica il nome del canale in current_extinf
        tvg_name_match = re.search(r'tvg-name="([^"]+)"', current_extinf)
        if tvg_name_match:
            tvg_name = tvg_name_match.group(1)
            # Estrai il nome del canale originale (ultima parte dopo la virgola)
            try:
                original_channel_name = current_extinf.split(",")[-1].strip()
                # Crea il nuovo titolo: tvg-name (original_channel_name)
                new_channel_name = f"{tvg_name} ({original_channel_name})"
                # Sostituisci il vecchio nome con il nuovo nella riga EXTINF
                new_extinf = ",".join(current_extinf.split(",")[:-1] + [new_channel_name])
                # Sostituisci l'EXTINF nella lista
                new_lines[-1] = new_extinf
            except IndexError:
                print(f"Errore nella riga EXTINF: {current_extinf}")
                new_lines[-1] = current_extinf  # Mantieni invariato in caso di errore
        else:
            print(f"tvg-name non trovato in: {current_extinf}")
        # Aggiungi l'URL modificato
        new_lines.append(modified_url)
        current_extinf = None
    else:
        new_lines.append(line)

# Salva il nuovo file M3U8
output_file = "itaevents3.m3u8"
try:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    print(f"File modificato salvato come {output_file}")
except Exception as e:
    print(f"Errore nel salvataggio del file: {e}")
