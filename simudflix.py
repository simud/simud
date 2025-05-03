import requests
from bs4 import BeautifulSoup

# URL principale del sito
main_url = "https://streamingcommunity.spa"

# Funzione per fare richiesta e ottenere l'HTML della pagina
def get_html(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

# Funzione per ottenere i link dalle categorie principali
def get_category_links():
    html = get_html(main_url)
    soup = BeautifulSoup(html, 'html.parser')

    # Estrai i link delle categorie principali dalla pagina principale
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

# Funzione per estrarre i flussi da una categoria
def extract_streaming_links_from_category(category_url):
    html = get_html(category_url)
    soup = BeautifulSoup(html, 'html.parser')

    # Trova tutti i film o episodi nella pagina della categoria
    # Adatta questo codice in base alla struttura dell'HTML
    video_links = []
    for link in soup.find_all('a', href=True):
        if 'watch' in link['href']:  # cerca link di streaming
            video_links.append(link['href'])
    
    return video_links

# Funzione per raccogliere tutti i flussi da tutte le categorie
def collect_streaming_links():
    category_links = get_category_links()
    all_streaming_links = {}

    # Per ogni categoria, estrai i link di streaming
    for category_name, category_url in category_links.items():
        print(f"Estraendo flussi dalla categoria: {category_name}")
        video_links = extract_streaming_links_from_category(category_url)
        all_streaming_links[category_name] = video_links

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