import requests
import os
import re

# URL della playlist M3U8
url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/channels_italy.m3u8"

# Nome del file di output
output_file = "vavoo.m3u8"

# Lista dei canali Primafila
primafila_channels = [
    "SKY PRIMAFILA 1 (V)", "SKY PRIMAFILA 2 (V)", "SKY PRIMAFILA 3 (V)", "SKY PRIMAFILA 4 (V)",
    "SKY PRIMAFILA 5 (V)", "SKY PRIMAFILA 6 (V)", "SKY PRIMAFILA 7 (V)", "SKY PRIMAFILA 8 (V)",
    "SKY PRIMAFILA 9 (V)", "SKY PRIMAFILA 10 (V)", "SKY PRIMAFILA 11 (V)", "SKY PRIMAFILA 12 (V)",
    "SKY PRIMAFILA 13 (V)", "SKY PRIMAFILA 14 (V)", "SKY PRIMAFILA 15 (V)", "SKY PRIMAFILA 16 (V)",
    "SKY PRIMAFILA 17 (V)", "SKY PRIMAFILA 18 (V)"
]

# Dettagli del canale ADMIN
admin_channel_template = '#EXTINF:-1 tvg-id="ADMIN" tvg-name="ADMIN" tvg-logo="https://i.postimg.cc/4ysKkc1G/photo-2025-03-28-15-49-45.png" group-title="{}","ADMIN"\nhttps://static.vecteezy.com/system/resources/previews/033/861/932/mp4/gherkins-close-up-loop-free-video.mp4'

try:
    # Scarica il contenuto del file M3U8
    response = requests.get(url)
    response.raise_for_status()  # Verifica se la richiesta è andata a buon fine
    
    # Leggi il contenuto
    content = response.text
    
    # Sostituisci le opzioni VLC
    content = content.replace(
        '#EXTVLCOPT:http-user-agent=VAVOO/2.6\n#EXTVLCOPT:http-referrer=https://vavoo.to/',
        '#EXTVLCOPT:http-user-agent=okhttp/4.11.0\n#EXTVLCOPT:http-origin=https://vavoo.to/\n#EXTVLCOPT:http-referrer=https://vavoo.to/'
    )
    
    # Trova tutti i gruppi esistenti
    groups = set()
    lines = content.splitlines()
    modified_lines = []
    
    for line in lines:
        if line.startswith('#EXTINF:'):
            # Estrai il nome del canale
            channel_match = re.search(r',\s*(.+?)\s*$', line)
            if channel_match:
                channel_name = channel_match.group(1).strip()
                modified_line = line
                
                # Estrai il group-title, se presente
                group_match = re.search(r'group-title="([^"]*)"', line)
                if group_match:
                    groups.add(group_match.group(1))
                
                # Gestisci i canali Primafila con "(V)" davanti
                primafila_match = re.match(r'\(V\)\s*(SKY PRIMAFILA \d{1,2})', channel_name)
                if primafila_match:
                    clean_channel_name = primafila_match.group(1)
                    if clean_channel_name in primafila_channels:
                        # Rimuovi "(V)" e assegna group-title="Primafila"
                        modified_line = re.sub(
                            r',\s*\(V\)\s*SKY PRIMAFILA \d{1,2}\s*$',
                            f',group-title="Primafila",{clean_channel_name}',
                            line
                        )
                        groups.add("Primafila")
                else:
                    # Rimuovi "(V)" alla fine per gli altri canali
                    modified_line = re.sub(r',\s*([^,]+)\s*\(V\)\s*$', r',\1', line)
                
                modified_lines.append(modified_line)
        else:
            modified_lines.append(line)
    
    # Aggiungi il canale ADMIN per ogni gruppo alla fine
    for group in sorted(groups):  # Ordino i gruppi per consistenza
        modified_lines.append(admin_channel_template.format(group))
    
    # Ricostruisci il contenuto
    modified_content = '\n'.join(modified_lines)
    
    # Salva il file modificato
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print(f"File modificato salvato con successo come: {output_file}")

except requests.exceptions.RequestException as e:
    print(f"Errore durante il download del file: {e}")
except Exception as e:
    print(f"Si è verificato un errore: {e}")
