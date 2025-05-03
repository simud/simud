import requests
from bs4 import BeautifulSoup

# URL principale del sito
main_url = "https://streamingcommunity.spa"

# Funzione per fare richiesta e ottenere l'HTML della pagina
def get_html(url):
    response = requests.get(url)
    response.raise_for_status()  # Se la risposta non è OK, solleva un errore
    return response.text

# Funzione per ottenere i link delle categorie principali
def get_category_links():
    html = get_html(main_url)
    soup = BeautifulSoup(html, 'html.parser')

    # Esegui l'analisi per ottenere i link alle categorie
    category_links = {
        "Top 10 di oggi": f"{main_url}/browse/top10",
        "I Titoli Del Momento": f"{main_url}/browse/trending",
        "Aggiunti di Recente": f"{main_url}/browse/latest",
        "Animazione": f"{main_url}/browse/genre?g=Animazione",
        "Avventura": f"{main_url}/browse/genre?g=Avventura",
        "Azione": f"{main_url}/browse/genre?g=Azione",
        "Commedia": f"{main_url}/browse/genre?g=Commedia",
        "Crime": f"{main_url}/browse/genre?g=Crime",
        "Documentario": f"{main_url}/browse/genre?g=Documentario",
        "Dramma": f"{main_url}/browse/genre?g=Dramma",
        "Famiglia": f"{main_url}/browse/genre?g=Famiglia",
        "Fantascienza": f"{main_url}/browse/genre?g=Fantascienza",
        "Fantasy": f"{main_url}/browse/genre?g=Fantasy",
        "Horror": f"{main_url}/browse/genre?g=Horror",
        "Reality": f"{main_url}/browse/genre?g=Reality",
        "Romance": f"{main_url}/browse/genre?g=Romance",
        "Thriller": f"{main_url}/browse/genre?g=Thriller",
    }
    return category_links

# Funzione per estrarre il link di streaming da una pagina di film o serie
def extract_streaming_link_from_page(page_url):
    html = get_html(page_url)
    soup = BeautifulSoup(html, 'html.parser')

    # Supponiamo che il flusso di streaming sia contenuto in un tag con class 'video-player' o simile
    # Modifica questo selettore in base alla struttura effettiva del sito
    video_tag = soup.find('video')
    if video_tag and video_tag.get('src'):
        return video_tag['src']  # Restituisce l'URL del flusso
    return None

# Funzione per estrarre i film/episodi dalla categoria
def extract_content_from_category(category_url):
    html = get_html(category_url)
    soup = BeautifulSoup(html, 'html.parser')

    content_links = []

    # Supponiamo che i film/episodi siano in tag 'a' con una certa classe
    # Devi adattare questa parte per riflettere correttamente il sito
    for link in soup.find_all('a', href=True):
        if '/watch/' in link['href']:  # Cerca link a contenuti specifici di film/serie
            content_links.append(f"{main_url}{link['href']}")

    return content_links

# Funzione principale per raccogliere i flussi da tutte le categorie
def collect_streaming_links():
    category_links = get_category_links()
    all_streaming_links = {}

    # Estrai i contenuti per ogni categoria e trova i flussi
    for category_name, category_url in category_links.items():
        print(f"Estraendo flussi dalla categoria: {category_name}")
        content_links = extract_content_from_category(category_url)
        
        category_streaming_links = []
        for content_link in content_links:
            print(f"  Estraendo flusso da: {content_link}")
            streaming_link = extract_streaming_link_from_page(content_link)
            if streaming_link:
                category_streaming_links.append(streaming_link)

        all_streaming_links[category_name] = category_streaming_links

    return all_streaming_links

# Funzione principale
def main():
    streaming_links = collect_streaming_links()
    for category, links in streaming_links.items():
        print(f"\nCategoria: {category}")
        for link in links:
            print(f"  - {link}")

if __name__ == "__main__":
    main()