import time
import httpx

# Funzione per ottenere i flussi validi
def get_valid_stream(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
    }

    try:
        with httpx.Client(follow_redirects=True, timeout=10, headers=headers) as client:
            response = client.get(url)
            if response.status_code == 200:
                return url
    except Exception as e:
        print(f"Errore durante la richiesta per {url}: {e}")
    
    return None

# Funzione per ottenere i flussi dei film
def get_movie_streams():
    movie_data = [
        ("Thunderbolts", "311493"),
        ("Iron Man 3", "253379"),
        ("Thor: Ragnarok", "146629"),
        ("Captain America: Civil War", "204967"),
        ("Black Panther: Wakanda Forever", "148685"),
        ("Spider-Man: No Way Home", "103166"),
        ("Doctor Strange nel Multiverso della Follia", "120723"),
        ("The Marvels", "186258")
    ]
    
    valid_streams = []
    
    for movie, playlist_id in movie_data:
        print(f"Controllo flusso per: {movie}")
        url = f"https://vixcloud.co/playlist/{playlist_id}?expires={int(time.time()) + 3600}&b=1&token=random_token&h=1"
        valid_url = get_valid_stream(url)
        if valid_url:
            valid_streams.append(f"#EXTINF:-1,{movie}\n{valid_url}")
        else:
            print(f"Film non trovato: {movie}")
    
    return valid_streams

# Scrivere la playlist M3U8
def create_m3u8_file(valid_streams):
    with open('streaming.m3u8', 'w') as f:
        f.write("#EXTM3U\n")
        for stream in valid_streams:
            f.write(stream + "\n")
    print("File M3U8 creato correttamente.")

def main():
    valid_streams = get_movie_streams()
    if valid_streams:
        create_m3u8_file(valid_streams)
    else:
        print("Nessun flusso valido trovato.")

if __name__ == "__main__":
    main()