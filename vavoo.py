import requests
import os
import re

# URL della playlist M3U8
url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/channels_italy.m3u8"

# Nome del file di output
output_file = "vavoo.m3u8"

# Lista dei canali Primafila
primafila_channels = [
    "Sky Primafila 1", "Sky Primafila 2", "Sky Primafila 3", "Sky Primafila 4",
    "Sky Primafila 5", "Sky Primafila 6", "Sky Primafila 7", "Sky Primafila 8",
    "Sky Primafila 9", "Sky Primafila 10", "Sky Primafila 11", "Sky Primafila 12",
    "Sky Primafila 13", "Sky Primafila 14", "Sky Primafila 15", "Sky Primafila 16",
    "Sky Primafila 17", "Sky Primafila 18"
]

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
    
    # Processa il file riga per riga
    lines = content.splitlines()
    modified_lines = []
    
    for line in lines:
        if line.startswith('#EXTINF:'):
            # Rimuovi "(V)" dal nome del canale dopo la virgola
            modified_line = re.sub(r',\s*([^,]+)\s*\(V\)\s*$', r',\1', line)
            
            # Controlla se il canale è nella lista Primafila
            channel_name = re.search(r',\s*([^,]+)\s*$', modified_line)
            if channel_name:
                channel_name = channel_name.group(1).strip()
                if channel_name in primafila_channels:
                    # Sostituisci o aggiungi group-title="Primafila"
                    if 'group-title="' in modified_line:
                        modified_line = re.sub(
                            r'group-title="[^"]*"',
                            'group-title="Primafila"',
                            modified_line
                        )
                    else:
                        # Aggiungi group-title se non esiste
                        modified_line = modified_line.replace(
                            channel_name,
                            f'group-title="Primafila",{channel_name}'
                        )
            
            modified_lines.append(modified_line)
        else:
            modified_lines.append(line)
    
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
