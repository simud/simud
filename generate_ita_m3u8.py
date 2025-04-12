name: Update Italian M3U8 Playlist

on:
  schedule:
    - cron: '0 0 * * *' # Esegue ogni giorno a mezzanotte UTC
  workflow_dispatch: # Permette l'esecuzione manuale

jobs:
  update-playlist:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests

      - name: Run script to generate M3U8
        run: python generate_ita_m3u8.py

      - name: Commit and push changes
        run: |
          git config --global user.name 'GitHub Action'
          git config --global user.email 'action@github.com'
          git add itaevents3.m3u8
          git commit -m "Update itaevents3.m3u8 with latest Italian channels" || echo "Nessuna modifica da commitare"
          git push
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
