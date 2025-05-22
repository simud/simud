import requests
import re

# URL della playlist originale
playlist_url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/247ita.m3u8"
# URL della playlist da concatenare
simudflix_url = "https://raw.githubusercontent.com/simud/simud/refs/heads/main/simudflix.m3u8"
# Base URL del proxy
proxy_base = "https://nzo66-tvproxy.hf.space/proxy/m3u?url="
# Nuovo logo per Canale 5
canale_5_logo = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Canale_5_-_2018_logo.svg/1222px-Canale_5_-_2018_logo.svg.png"

# Canali da eliminare
channels_to_remove = [
    "Sky Cinema Uno +24",
    "Sky Cinema Due +24",
    "Rai Premium",
    "Sky Calcio 6",
    "Sky Calcio 7",
    "LA7d"
]

# Mappatura per la sostituzione dei flussi (simudflix -> 247ita)
channel_replacements = {
    "Sky Uno": "Sky UNO",
    "Sky Sport Uno": "Sky Sport UNO",
    "Sky Sport Max": "Sky Sport Football",
    "Sky Sport Golf": "Sky Sports Golf",
    "La7 HD": "La7",
    "DAZN 1 HD": "DAZN 1",
    "Sky Calcio 1 (251)": "Sky Calcio 1",
    "Sky Calcio 2 (252)": "Sky Calcio 2",
    "Sky Calcio 3 (253)": "Sky Calcio 3",
    "Sky Calcio 4 (254)": "Sky Calcio 4"
}

def clean_channel_name(name):
    """Pulisce il nome del canale rimuovendo FHD e (D) per il confronto."""
    name = re.sub(r'\s*FHD$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(D\)$', '', name, flags=re.IGNORECASE)
    return name.strip()

def has_fhd(name):
    """Verifica se il nome del canale contiene già FHD."""
    return bool(re.search(r'\s*FHD$', name, flags=re.IGNORECASE))

def transform_group(current_group, channel_name):
    """Trasforma il nome del gruppo secondo le regole specificate."""
    cleaned_channel = clean_channel_name(channel_name)
    if cleaned_channel == "Rai Sport":
        return "Rai"
    if cleaned_channel == "DAZN 1":
        return "DAZN Serie A"
    if current_group in ["Tv Italia", "Rai Tv", "Mediaset"]:
        return "Rai"
    if current_group == "Sky":
        return "Sky Cinema FHD"
    if current_group == "Sport":
        return "Sky Sport FHD"
    return current_group

def update_extinf(extinf, channel_name):
    """Aggiorna il group-title nell'extinf usando transform_group."""
    group_pattern = r'group-title="([^"]*)"'
    group_match = re.search(group_pattern, extinf, re.IGNORECASE)
    new_group = transform_group(group_match.group(1) if group_match else "", channel_name)
    if group_match:
        updated_extinf = re.sub(group_pattern, f'group-title="{new_group}"', extinf, flags=re.IGNORECASE)
    else:
        updated_extinf = f'{extinf} group-title="{new_group}"'
    original_group = group_match.group(1) if group_match else "nessuno"
    print(f"Trasformazione gruppo per '{channel_name}': '{original_group}' -> '{new_group}'")
    return updated_extinf

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

        # Processa la playlist originale per creare un dizionario di canali trasformati
        original_channels = {}
        original_lines = original_content.splitlines()
        i = 0
        while i < len(original_lines):
            line = original_lines[i].strip()
            if line.startswith("#EXTINF"):
                match = re.match(r'(#EXTINF:.*?),\s*(.+?)\s*(\(D\))?\s*$', line)
                if match:
                    extinf = match.group(1)
                    channel_name = match.group(2).strip()
                    extinf_lines = [line]
                    j = i + 1
                    while j < len(original_lines) and original_lines[j].startswith("#EXTVLCOPT"):
                        extinf_lines.append(original_lines[j].strip())
                        j += 1
                    stream_url = original_lines[j].strip() if j < len(original_lines) and not original_lines[j].startswith("#") else None

                    # Trasforma il gruppo
                    extinf = update_extinf(extinf, channel_name)

                    # Modifica per Rai 3 -> Canale 5
                    if channel_name == "Rai 3":
                        channel_name = "Canale 5"
                        if 'tvg-logo="' in extinf:
                            extinf = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{canale_5_logo}"', extinf)
                        else:
                            extinf = extinf.replace('tvg-name="Rai 3"', f'tvg-name="Canale 5" tvg-logo="{canale_5_logo}"')
                        extinf = re.sub(r'tvg-name="[^"]*"', f'tvg-name="Canale 5"', extinf)

                    # Aggiungi FHD al nome del canale per 247ita, se non presente
                    new_channel_name = channel_name if has_fhd(channel_name) else f"{channel_name} FHD"

                    # Salva il canale trasformato
                    cleaned_name = clean_channel_name(channel_name)
                    transformed_url = proxy_base + stream_url if stream_url else None
                    original_channels[cleaned_name] = (extinf_lines, transformed_url, new_channel_name)

                    i = j + 1 if stream_url else j
                    continue
                else:
                    i += 1
            else:
                i += 1

        # Salva la nuova playlist
        output_file = "simudflix2.m3u8"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")

            # Processa la playlist simudflix
            simudflix_lines = simudflix_content.splitlines()
            i = 0
            written_channels = set()
            while i < len(simudflix_lines):
                line = simudflix_lines[i].strip()
                if line.startswith("#EXTINF"):
                    match = re.match(r'(#EXTINF:.*?),\s*(.+?)\s*$', line)
                    if match:
                        extinf = match.group(1)
                        channel_name = match.group(2).strip()
                        extinf_lines = [line]
                        j = i + 1
                        while j < len(simudflix_lines) and simudflix_lines[j].startswith("#EXTVLCOPT"):
                            extinf_lines.append(simudflix_lines[j].strip())
                            j += 1
                        stream_url = simudflix_lines[j].strip() if j < len(simudflix_lines) and not simudflix_lines[j].startswith("#") else None

                        cleaned_name = clean_channel_name(channel_name)
                        # Per simudflix, mantieni il nome originale senza aggiungere FHD
                        new_channel_name = channel_name

                        # Trasforma il gruppo per simudflix
                        extinf = update_extinf(extinf, cleaned_name)

                        # Controlla se il canale deve essere sostituito
                        replacement_channel = channel_replacements.get(cleaned_name)
                        if replacement_channel and replacement_channel in original_channels:
                            # Usa i metadati di simudflix, ma il flusso e il nome da 247ita
                            orig_extinf_lines, orig_stream, orig_channel_name = original_channels[replacement_channel]
                            if cleaned_name not in channels_to_remove:
                                for extinf_line in extinf_lines:
                                    if extinf_line.startswith("#EXTINF"):
                                        new_extinf = update_extinf(extinf_line.split(',')[0], cleaned_name)
                                        f.write(f"{new_extinf},{orig_channel_name}\n")
                                    else:
                                        f.write(extinf_line + "\n")
                                f.write(orig_stream + "\n")
                            written_channels.add(replacement_channel)
                        elif stream_url and stream_url.startswith("https://dproxy-o.hf.space/stream/") and cleaned_name in original_channels:
                            # Sostituisci il flusso dproxy con quello originale
                            orig_extinf_lines, orig_stream, orig_channel_name = original_channels[cleaned_name]
                            if cleaned_name not in channels_to_remove:
                                for orig_line in orig_extinf_lines:
                                    if orig_line.startswith("#EXTINF"):
                                        new_extinf = update_extinf(orig_line.split(',')[0], cleaned_name)
                                        f.write(f"{new_extinf},{orig_channel_name}\n")
                                    else:
                                        f.write(orig_line + "\n")
                                f.write(orig_stream + "\n")
                            written_channels.add(cleaned_name)
                        else:
                            # Mantieni il canale di simudflix invariato
                            if cleaned_name not in channels_to_remove:
                                for extinf_line in extinf_lines:
                                    if extinf_line.startswith("#EXTINF"):
                                        new_extinf = update_extinf(extinf_line.split(',')[0], cleaned_name)
                                        f.write(f"{new_extinf},{new_channel_name}\n")
                                    else:
                                        f.write(extinf_line + "\n")
                                if stream_url:
                                    f.write(stream_url + "\n")

                        i = j + 1 if stream_url else j
                        continue
                    else:
                        f.write(line + "\n")
                else:
                    f.write(line + "\n")
                i += 1

            # Aggiungi i canali della playlist originale non ancora scritti
            for cleaned_name, (extinf_lines, stream_url, new_channel_name) in original_channels.items():
                if cleaned_name not in written_channels and cleaned_name not in channels_to_remove:
                    for extinf_line in extinf_lines:
                        if extinf_line.startswith("#EXTINF"):
                            new_extinf = update_extinf(extinf_line.split(',')[0], cleaned_name)
                            f.write(f"{new_extinf},{new_channel_name}\n")
                        else:
                            f.write(extinf_line + "\n")
                    if stream_url:
                        f.write(stream_url + "\n")

        print(f"Playlist trasformata e concatenata salvata come {output_file}")

        # Debug: verifica i group-title nel file generato
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("#EXTINF"):
                    group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
                    if group_match:
                        group = group_match.group(1)
                        if group in ["Tv Italia", "Rai Tv", "Mediaset", "Sky", "Sport"]:
                            print(f"Attenzione: trovato group-title non trasformato '{group}' in: {line.strip()}")
                        if "Rai Sport" in line and group != "Rai":
                            print(f"Attenzione: 'Rai Sport' ha group-title errato '{group}' in: {line.strip()}")

    except requests.RequestException as e:
        print(f"Errore nel scaricare una delle playlist: {e}")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    transform_m3u8()
