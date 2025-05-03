from scuapi import API

titles = [
    "John Wick",
    "Breaking Bad",
    "Oppenheimer",
    "Avatar",
    "Stranger Things"
]

sc = API("streamingcommunity.spa")

with open("streaming.m3u8", "w", encoding="utf-8") as file:
    file.write("#EXTM3U\n")
    for title in titles:
        try:
            print(f"Cercando: {title}")
            results = sc.search(title)
            first_result = next(iter(results.values()))
            url = first_result["url"].geturl()  # CORRETTO: Convertiamo ParseResult in stringa URL
            iframe, m3u8 = sc.get_links(url)
            file.write(f"#EXTINF:-1,{title}\n{m3u8}\n")
            print(f"  Aggiunto: {m3u8}")
        except Exception as e:
            print(f"  Errore per {title}: \n\t{e}")