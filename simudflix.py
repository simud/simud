import requests
from bs4 import BeautifulSoup

# URL della homepage
url = "https://altadefinizionegratis.sbs"

# Intestazione dell'user-agent per evitare che venga bloccato come bot
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Effettua la richiesta alla pagina
response = requests.get(url, headers=headers)

# Verifica che la richiesta sia andata a buon fine
if response.status_code == 200:
    print("Pagina recuperata con successo!")
    soup = BeautifulSoup(response.content, 'html.parser')

    # Trova tutti i link che corrispondono alla struttura dei film (che contengono 'streaming' o 'gratis' nel nome)
    movie_links = []
    
    # Trova tutti i collegamenti dalla home page
    for link in soup.find_all('a', href=True):
        link_text = link.text.strip().lower()
        
        # Se il testo del link contiene parole come 'streaming', 'gratis' o simili
        if ('streaming' in link_text and 'gratis' in link_text) or 'streaming' in link_text:
            movie_links.append(link['href'])

        # Limita il numero di link a 50
        if len(movie_links) >= 50:
            break

    # Stampa i primi 50 link
    if movie_links:
        print("Primi 50 link trovati:")
        for i, link in enumerate(movie_links, 1):
            print(f"{i}. {link}")
    else:
        print("Nessun link trovato che corrisponda ai criteri.")
else:
    print(f"Errore nella richiesta della pagina: {response.status_code}")