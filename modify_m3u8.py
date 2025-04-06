import requests
import re
from github import Github
import os

def get_m3u8_content(url):
    response = requests.get(url)
    return response.text

def extract_headers(m3u8_content):
    headers = {
        'Referer': None,
        'Origin': None,
        'User-Agent': None
    }
    referer_match = re.search(r'#EXTINF:.*?-referer="([^"]+)"', m3u8_content)
    origin_match = re.search(r'#EXTINF:.*?-origin="([^"]+)"', m3u8_content)
    ua_match = re.search(r'#EXTINF:.*?-user-agent="([^"]+)"', m3u8_content)
    
    if referer_match:
        headers['Referer'] = referer_match.group(1)
    if origin_match:
        headers['Origin'] = origin_match.group(1)
    if ua_match:
        headers['User-Agent'] = ua_match.group(1)
    return headers

def modify_m3u8(source_content, headers):
    lines = source_content.split('\n')
    modified_lines = []
    
    for line in lines:
        if line.startswith('#EXTINF:'):
            line = re.sub(r' -referer="[^"]+"', '', line)
            line = re.sub(r' -origin="[^"]+"', '', line)
            line = re.sub(r' -user-agent="[^"]+"', '', line)
            if headers['Referer']:
                line += f' -referer="{headers["Referer"]}"'
            if headers['Origin']:
                line += f' -origin="{headers["Origin"]}"'
            if headers['User-Agent']:
                line += f' -user-agent="{headers["User-Agent"]}"'
        modified_lines.append(line)
    return '\n'.join(modified_lines)

def main():
    source_url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/itaevents.m3u8"
    headers_url = "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/daddylive-channels.m3u8"
    
    print("Scaricamento delle liste...")
    source_content = get_m3u8_content(source_url)
    headers_content = get_m3u8_content(headers_url)
    
    headers = extract_headers(headers_content)
    modified_content = modify_m3u8(source_content, headers)
    
    # Salva localmente per il commit
    with open('itaevents2.m3u8', 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("File itaevents2.m3u8 aggiornato localmente")
    print("Header applicate:")
    for key, value in headers.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
