import requests
import re

def get_m3u8_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Errore nel download da {url}: {e}")
        return None

def extract_headers(m3u8_content):
    if not m3u8_content:
        return {'Referer': None, 'Origin': None, 'User-Agent': None}
    
    headers = {'Referer': None, 'Origin': None, 'User-Agent': None}
    
    referer_match = re.search(r'#EXTVLCOPT:http-referrer=(.+)', m3u8_content)
    origin_match = re.search(r'#EXTVLCOPT:http-origin=(.+)', m3u8_content)
    ua_match = re.search(r'#EXTVLCOPT:http-user-agent=(.+)', m3u8_content)
    
    if referer_match:
        headers['Referer'] = referer_match.group(1).strip()
    if origin_match:
        headers['Origin'] = origin_match.group(1).strip()
    if ua_match:
        headers['User-Agent'] = ua_match.group(1).strip()
    
    print("Header estratte:")
    for key, value in headers.items():
        print(f"{key}: {value or 'Non presente'}")
    
    return headers

def modify_m3u8(source_content, headers):
    if not source_content:
        return ""
    
    lines = source_content.split('\n')
    modified_lines = []
    
    for line in lines:
        if line.startswith('#EXTINF:'):
            # Estrai il tvg-name e il nome del canale
            tvg_match = re.search(r'tvg-name="([^"]+)"', line)
            channel_match = re.search(r',\s*([^,]+)$', line)
            
            if tvg_match and channel_match:
                tvg_name = tvg_match.group(1)
                channel_name = channel_match.group(1).strip()
                # Sostituisci il nome del canale con tvg-name (channel_name)
                modified_line = line.replace(f',{channel_name}', f',{tvg_name} ({channel_name})')
                modified_lines.append(modified_line)
                print(f"Modificato: {tvg_name} ({channel_name})")
            else:
                modified_lines.append(line)
                
            # Aggiungi le header dopo EXTINF
            if headers['Origin']:
                modified_lines.append(f'#EXTVLCOPT:http-origin={headers["Origin"]}')
            if headers['Referer']:
                modified_lines.append(f'#EXTVLCOPT:http-referrer={headers["Referer"]}')
            if headers['User-Agent']:
                modified_lines.append(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}')
            print(f"Aggiunte header dopo EXTINF: {line}")
            
        elif line.startswith('#EXTVLCOPT:http-'):
            # Ignora le righe EXTVLCOPT esistenti
            continue
        else:
            # Mantieni tutte le altre righe (incluso #EXTM3U e URL)
            modified_lines.append(line)
    
    return '\n'.join(modified_lines)

def main():
    source_url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/itaevents.m3u8"
    headers_url = "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/daddylive-channels.m3u8"
    
    print("Scaricamento delle liste...")
    source_content = get_m3u8_content(source_url)
    headers_content = get_m3u8_content(headers_url)
    
    if source_content is None or headers_content is None:
        print("Errore: impossibile procedere a causa di problemi di download")
        return
    
    headers = extract_headers(headers_content)
    modified_content = modify_m3u8(source_content, headers)
    
    with open('itaevents2.m3u8', 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("File itaevents2.m3u8 aggiornato con successo")

if __name__ == "__main__":
    main()
