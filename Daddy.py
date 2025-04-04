import requests
import os
from pathlib import Path
import base64

def push_to_github(content, repo_owner, repo_name, file_path, token):
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(api_url, headers=headers)
    sha = response.json().get("sha") if response.status_code == 200 else None
    data = {
        "message": "Update combined_playlist.m3u8",
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        "branch": "main"
    }
    if sha:
        data["sha"] = sha
    response = requests.put(api_url, headers=headers, json=data)
    if response.status_code in [200, 201]:
        print(f"File caricato con successo su GitHub: {file_path}")
    else:
        print(f"Errore nel caricare il file: {response.status_code} - {response.text}")

def concatenate_and_push_m3u8():
    urls = [
        "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/daddylive-channels.m3u8",
        "https://raw.githubusercontent.com/simud/simud/refs/heads/main/sportstreaming_playlist.m3u8"
    ]
    repo_owner = "simud"
    repo_name = "simud"
    file_path = "combined_playlist.m3u8"
    token = os.getenv("secrets.ACTIONS_TOKEN")
    if not token:
        print("Errore: Imposta la variabile d'ambiente ACTIONS_TOKEN con il tuo GitHub token.")
        return
    combined_content = ["#EXTM3U"]
    for url in urls:
        try:
            print(f"Tentativo di scaricare: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            lines = response.text.splitlines()
            print(f"Scaricate {len(lines)} righe da {url}")
            for line in lines:
                line = line.strip()
                if line and line != "#EXTM3U":
                    combined_content.append(line)
        except requests.RequestException as e:
            print(f"Errore nel scaricare {url}: {str(e)}")
            return
    final_content = "\n".join(combined_content)
    print(f"Totale righe da caricare: {len(combined_content)}")
    push_to_github(final_content, repo_owner, repo_name, file_path, token)

if __name__ == "__main__":
    concatenate_and_push_m3u8()
