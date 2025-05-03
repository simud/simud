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

# Funzione per estrarre il flusso di streaming da una pagina di film o serie
def extract_streaming_link_from_page(page_url):
    html = get_html(page_url)
    soup = BeautifulSoup(html, 'html.parser')

    # Supponiamo che il flusso M3U8 sia in un tag <video> o <source> o simile
    # Aggiusta questa parte in base alla struttura della pagina effettiva
    video_tag = soup.find('video')
    if video_tag:
        m3u8_link = video_tag.find('source', type="application/x-mpegURL")
        if m3u8_link:
            return m3u8_link['src']
    return None

# Funzione per estrarre i link di film/episodi dalla pagina della categoria
def extract_content_from_category(category_url):
    html = get_html(category_url)
    soup = BeautifulSoup(html, 'html.parser')

    content_links = []

    # Supponiamo che i link ai contenuti siano in tag <a> con un URL che contiene '/watch/'
    # Modifica questo selettore in base alla struttura effettiva del sito
    for link in soup.find_all('a', href=True):
        if '/watch/' in link['href']:  # Cerca i link relativi ai contenuti
            content_links.append(f"{main_url}{link['href']}")

    return content_links

# Funzione per raccogliere i flussi per tutte le categorie
def collect_streaming_links():
    category_links = get_category_links()
    all_streaming_links = {}

    # Estrazione dei contenuti da ciascuna categoria
    for category_name, category_url in category_links.items():
        print(f"Estraendo flussi dalla categoria: {category_name}")
        content_links = extract_content_from_category(category_url)
        
        category_streaming_links = []
        for content_link in content_links:
            print(f"  Estraendo flusso da: {content_link}")
            streaming_link = extract_streaming_link_from_page(content_link)
            if streaming_link:
                category_streaming_links.append(streaming_link)

        # Aggiungi i flussi della categoria
        all_streaming_links[category_name] = category_streaming_links

    return all_streaming_links

# Funzione principale
def main():
    streaming_links = collect_streaming_links()
    for category, links in streaming_links.items():
        print(f"\nCategoria: {category}")
        if links:
            for link in links:
                print(f"  - {link}")
        else:
            print("  Nessun flusso trovato.")

if __name__ == "__main__":
    main()