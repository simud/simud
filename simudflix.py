import asyncio
import time
import httpx

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

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
}

async def get_valid_stream(client, movie, playlist_id):
    expires = int(time.time()) + 3600
    token = "random_token"  # Puoi migliorarlo se serve
    url = f"https://vixcloud.co/playlist/{playlist_id}?expires={expires}&b=1&token={token}&h=1"

    try:
        response = await client.get(url, timeout=10)
        if response.status_code == 200:
            print(f"Flusso valido per: {movie}")
            return f"#EXTINF:-1,{movie}\n{url}"
        else:
            print(f"Flusso non valido per: {movie}")
    except Exception as e:
        print(f"Errore durante la richiesta per {movie}: {e}")
    return None

async def get_movie_streams():
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        tasks = [get_valid_stream(client, movie, playlist_id) for movie, playlist_id in movie_data]
        results = await asyncio.gather(*tasks)
        return [stream for stream in results if stream]

def create_m3u8_file(valid_streams):
    with open('streaming.m3u8', 'w') as f:
        f.write("#EXTM3U\n")
        for stream in valid_streams:
            f.write(stream + "\n")
    print("File M3U8 creato correttamente.")

def main():
    valid_streams = asyncio.run(get_movie_streams())
    if valid_streams:
        create_m3u8_file(valid_streams)
    else:
        print("Nessun flusso valido trovato.")

if __name__ == "__main__":
    main()