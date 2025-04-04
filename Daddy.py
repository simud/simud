name: Create Combined M3U8 Playlist

on:
  workflow_dispatch:  # Esecuzione manuale
  # schedule:
  #   - cron: '0 0 * * *'  # Uncomment per esecuzione giornaliera a mezzanotte UTC

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install requests
        run: pip install requests

      - name: Create and push combined M3U8
        run: |
          python - <<EOF
          import requests
          import base64
          import os

          # URL delle liste
          urls = [
              "https://raw.githubusercontent.com/pigzillaaaaa/iptv-scraper/refs/heads/main/daddylive-channels.m3u8",
              "https://raw.githubusercontent.com/simud/simud/refs/heads/main/sportstreaming_playlist.m3u8"
          ]
          
          # Configurazione GitHub
          repo_owner = "simud"
          repo_name = "simud"
          file_path = "combined_playlist.m3u8"
          token = "${{ secrets.ACTIONS_TOKEN }}"  # Usa il segreto ACTIONS_TOKEN

          # Crea il contenuto combinato
          combined_content = ["#EXTM3U"]
          for url in urls:
              try:
                  response = requests.get(url, timeout=10)
                  response.raise_for_status()
                  lines = response.text.splitlines()
                  print(f"Scaricate {len(lines)} righe da {url}")
                  for line in lines:
                      line = line.strip()
                      if line and line != "#EXTM3U":
                          combined_content.append(line)
              except Exception as e:
                  print(f"Errore nel scaricare {url}: {e}")
                  exit(1)

          final_content = "\n".join(combined_content)
          print(f"Totale righe da caricare: {len(combined_content)}")

          # Interazione con l'API di GitHub
          api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
          headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
          response = requests.get(api_url, headers=headers)
          sha = response.json().get("sha") if response.status_code == 200 else None
          
          data = {
              "message": "Update combined_playlist.m3u8",
              "content": base64.b64encode(final_content.encode('utf-8')).decode('utf-8'),
              "branch": "main"
          }
          if sha:
              data["sha"] = sha
          
          response = requests.put(api_url, headers=headers, json=data)
          if response.status_code in [200, 201]:
              print("File caricato con successo su GitHub")
          else:
              print(f"Errore nel caricare il file: {response.status_code} - {response.text}")
              exit(1)
          EOF
