import requests
import re

# URL della playlist originale
playlist_url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/247ita.m3u8"
# URL della playlist da concatenare
simudflix_url = "https://raw.githubusercontent.com/simud/simud/refs/heads/main/simudflix.m3u8"
# Base URL del proxy
proxy_base = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d="
# Nuovo logo per Canale 5
canale_5_logo = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Canale_5_-_2018_logo.svg/1222px-Canale_5_-_2018_logo.svg.png"

def clean_channel_name(name):
    """Pulisce il nome del canale rimuovendo FHD e (D) per il confronto."""
    name = re.sub(r'\s*FHD$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(D\)$', '', name, flags=re.IGNORECASE)
    return name.strip()

def transform_m3u8():
    try:
        # Scarica la playlist originale
        response = requests.get(playlist_url)
        response.raise_for_status()
        original_content = response.text

        # Scarica la playlist simudflix
        response = requests.get(simudflix_url)
        response.raise_for_status()
        simudflix_content = response.text

        # Processa la playlist simudflix per estrarre i canali con flusso dproxy
        simudflix_channels = {}
        simudflix_lines = simudflix_content.splitlines()
        i = 0
        while i < len(simudflix_lines):
            line = simudflix_lines[i].strip()
            if line.startswith("#EXTINF"):
                match = re.match(r'(#EXTINF:.*?),\s*(.+?)\s*$', line)
                if match and i + 1 < len(simudflix_lines):
                    extinf = line
                    stream_url = simudflix_lines[i + 1].strip()
                    if stream_url.startswith("https://dproxy-o.hf.space/stream/"):
                        channel_name = clean_channel_name(match.group(2))
                        simudflix_channels[channel_name] = (extinf, stream_url)
                i += 1
            else:
                i += 1

        # Salva la nuova playlist
        output_file = "simudflix2.m3u8"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Scrivi l'intestazione M3U
            f.write("#EXTM3U\n")
            
            # Processa la playlist originale
            lines = original_content.splitlines()
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Modifica le righe #EXTINF
                if line.startswith("#EXTINF"):
                    match = re.match(r'(#EXTINF:.*?),\s*(.+?)\s*(\(D\))?\s*$', line)
                    if match:
                        extinf = match.group(1)  # Parte #EXTINF con attributi
                        channel_name = match.group(2).strip()  # Nome del canale
                        
                        # Modifica il gruppo
                        group_pattern = r'group-title="([^"]*)"'
                        group_match = re.search(group_pattern, extinf)
                        if group_match:
                            current_group = group_match.group(1)
                            if current_group in ["TV Italia", "Mediaset", "Rai TV"]:
                                extinf = re.sub(group_pattern, 'group-title="Rai"', extinf)
                            elif current_group == "Sky":
                                extinf = re.sub(group_pattern, 'group-title="Sky Cinema FHD"', extinf)
                            elif current_group == "Sport":
                                extinf = re.sub(group_pattern, 'group-title="Sky Sport FHD"', extinf)
                        
                        # Modifica per Rai 3 -> Canale 5
                        if channel_name == "Rai 3":
                            channel_name = "Canale 5"
                            # Aggiorna il logo
                            if 'tvg-logo="' in extinf:
                                extinf = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{canale_5_logo}"', extinf)
                            else:
                                extinf = extinf.replace('tvg-name="Rai 3"', f'tvg-name="Canale 5" tvg-logo="{canale_5_logo}"')
                            # Aggiorna tvg-name
                            extinf = re.sub(r'tvg-name="[^"]*"', f'tvg-name="Canale 5"', extinf)
                        
                        # Aggiungi FHD al nome del canale
                        new_channel_name = f"{channel_name} FHD"
                        
                        # Controlla se il canale esiste in simudflix con flusso dproxy
                        cleaned_name = clean_channel_name(channel_name)
                        if cleaned_name in simudflix_channels:
                            # Usa la riga EXTINF e il flusso da simudflix
                            simud_extinf, simud_stream = simudflix_channels[cleaned_name]
                            # Aggiorna il nome del canale in simudflix per includere FHD
                            simud_match = re.match(r'(#EXTINF:.*?),\s*(.+?)\s*$', simud_extinf)
                            if simud_match:
                                simud_extinf = simud_match.group(1)
                                f.write(f"{simud_extinf},{new_channel_name}\n")
                                f.write(simud_stream + "\n")
                            else:
                                # Fallback: usa la riga originale trasformata
                                f.write(f"{extinf},{new_channel_name}\n")
                                # Trasforma l'URL originale con il proxy
                                if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                                    transformed_url = proxy_base + lines[i + 1].strip()
                                    f.write(transformed_url + "\n")
                            i += 2  # Salta la riga del flusso
                            continue
                        
                        # Ricostruisci la riga originale trasformata
                        f.write(f"{extinf},{new_channel_name}\n")
                    else:
                        # Scrivi la riga invariata se non trova il nome
                        f.write(line + "\n")
                
                # Trasforma le righe con URL dei flussi (se non già gestite)
                elif line and not line.startswith("#"):
                    transformed_url = proxy_base + line
                    f.write(transformed_url + "\n")
                
                # Scrivi altre righe di metadati invariate
                else:
                    f.write(line + "\n")
                
                i += 1
            
            # Concatena i canali di simudflix che non sono stati usati
            for channel_name, (extinf, stream_url) in simudflix_channels.items():
                # Verifica se il canale è già stato scritto
                already_written = any(
                    clean_channel_name(line.split(",")[-1]) == channel_name
                    for line in original_content.splitlines()
                    if line.startswith("#EXTINF")
                )
                if not already_written:
                    # Aggiungi FHD al nome del canale
                    match = re.match(r'(#EXTINF:.*?),\s*(.+?)\s*$', extinf)
                    if match:
                        simud_extinf = match.group(1)
                        simud_channel_name = match.group(2).strip()
                        new_channel_name = f"{simud_channel_name} FHD"
                        f.write(f"{simud_extinf},{new_channel_name}\n")
                        f.write(stream_url + "\n")
        
        print(f"Playlist trasformata e concatenata salvata come {output_file}")
        
    except requests.RequestException as e:
        print(f"Errore nel scaricare una delle playlist: {e}")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    transform_m3u8()
