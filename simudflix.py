import asyncio
from mediaflow_proxy.extractors.vixcloud import VixCloudExtractor

marvel_titles = [
    "Iron Man", "The Avengers", "Captain America", "Thor",
    "Black Panther", "Doctor Strange", "Guardiani della Galassia",
    "Spider-Man", "Ant-Man", "Captain Marvel"
]

# URL base dei contenuti su streamingcommunity (simulato per l'esempio)
BASE_URL = "https://streamingcommunity.spa/watch/"

# Mappa titoli a ID contenuto (dovresti avere un modo per recuperarli dinamicamente)
title_id_map = {
    "Iron Man": "1001",
    "The Avengers": "1002",
    "Captain America": "1003",
    "Thor": "1004",
    "Black Panther": "1005",
    "Doctor Strange": "1006",
    "Guardiani della Galassia": "1007",
    "Spider-Man": "1008",
    "Ant-Man": "1009",
    "Captain Marvel": "1010"
}

async def extract_playlist_url(title: str, content_id: str, extractor: VixCloudExtractor):
    try:
        url = f"{BASE_URL}{content_id}"
        result = await extractor.extract(url)
        return title, result["destination_url"]
    except Exception as e:
        print(f"Fallito: {title} - {e}")
        return title, None

async def main():
    extractor = VixCloudExtractor()
    tasks = [
        extract_playlist_url(title, title_id_map[title], extractor)
        for title in marvel_titles
    ]
    results = await asyncio.gather(*tasks)

    with open("streaming.m3u8", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for title, url in results:
            if url:
                f.write(f"#EXTINF:-1,{title}\n{url}\n")
                print(f"Successo: {title}")
            else:
                print(f"Fallito: {title}")

if __name__ == "__main__":
    asyncio.run(main())