import requests
 import os
 import re
 
 # URL della playlist M3U8
 url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/channels_italy.m3u8"
 
 # Nome del file di output
 output_file = "vavoo.m3u8"
 
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
     
     # Processa il file riga per riga per rimuovere "(V)" dai nomi dei canali
     lines = content.splitlines()
     modified_lines = []
     
     for line in lines:
         if line.startswith('#EXTINF:'):
             # Rimuovi "(V)" dal nome del canale dopo la virgola
             modified_line = re.sub(r',\s*([^,]+)\s*\(V\)\s*$', r',\1', line)
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
