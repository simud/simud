import requests
from bs4 import BeautifulSoup

# URL del sito che vogliamo analizzare
url = "https://altadefinizionegratis.sbs/"

# Invia una richiesta GET alla pagina
response = requests.get(url)

# Controlla se la richiesta è stata effettuata correttamente
if response.status_code == 200:
    # Analizza il contenuto HTML con BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Cerca un video o un tag con il link al flusso
    # Qui cerchiamo direttamente un possibile link al flusso video
    video_tag = soup.find("video")  # Modifica se necessario, a seconda della struttura della pagina
    
    if video_tag:
        # Estrai l'URL dal tag video
        video_url = video_tag.get("src")
        print("Video URL trovato:", video_url)
    else:
        print("Nessun tag video trovato nella pagina.")
    
else:
    print("Errore nella richiesta:", response.status_code)