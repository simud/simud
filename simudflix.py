import requests
import os

# Funzione per invertire i parametri di expires e token
def invert_parameters(url):
    # Suddividi la query string della URL
    base_url, query = url.split('?')
    params = dict(p.split('=') for p in query.split('&'))

    # Inverti expires e token
    if 'expires' in params and 'token' in params:
        params['expires'], params['token'] = params['token'], params['expires']

    # Ricostruisci la URL con i parametri invertiti
    new_query = '&'.join([f"{key}={value}" for key, value in params.items()])
    return base_url + '?' + new_query

# Funzione per ottenere nuovi flussi (simulazione)
def get_new_flows():
    # Lista di flussi di esempio (da sostituire con API reali o logica di scraping)
    flows = [
        {"title": "Thunderbolts", "url": "https://vixcloud.co/playlist/311493?b=1&expires=1751470092&token=b712d13b7d8da879f1360276c763eb18&h=1"},
        {"title": "Iron Man 3", "url": "https://vixcloud.co/playlist/253379?expires=1751469914&token=80b4c58e91791216c0c1189cdb13838c&h=1"},
        {"title": "Thor: Ragnarok", "url": "https://vixcloud.co/playlist/146629?expires=1751469915&token=491fb259e7c21586efb75d2cf05b403e&h=1"},
        # Aggiungi altri flussi qui
    ]

    # Inverti i parametri di expires e token per ogni flusso
    for flow in flows:
        flow['url'] = invert_parameters(flow['url'])

    return flows

# Funzione per scrivere i flussi nel file M3U8
def write_to_m3u8(flows, file_path='streaming.m3u8'):
    with open(file_path, 'w') as file:
        file.write('#EXTM3U\n')  # Header del file M3U8

        for flow in flows:
            file.write(f"#EXTINF:-1,{flow['title']}\n")
            file.write(f"#EXTVLCOPT:http-referrer=https://StreamingCommunity.spa\n")
            file.write(f"#EXTVLCOPT:http-origin=https://StreamingCommunity.spa\n")
            file.write(f"#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1\n")
            file.write(f"{flow['url']}\n")

# Esegui lo scraper
def main():
    new_flows = get_new_flows()  # Ottieni nuovi flussi
    write_to_m3u8(new_flows)     # Scrivi nel file M3U8

if __name__ == "__main__":
    main()