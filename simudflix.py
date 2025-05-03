from scuapi import API

# Lista dei titoli da cercare
titles = [
    "John Wick",
    "Breaking Bad",
    "Oppenheimer",
    "Avatar",
    "Stranger Things"
]

# Inizializza API con il dominio corretto
sc = API("streamingcommunity.spa")

# File M3U8 da scrivere
with open("streaming.m3u8", "w", encoding="utf-8") as file:
    file.write("#EXTM3U\n")
    for title in titles:
        try:
            print(f"Cercando: {title}")
            results = sc.search(title)
            first_result = next(iter(results.values()))
            iframe, m3u8 = sc.get_links(first_result["url"])
            file.write(f"#EXTINF:-1,{title}\n{m3u8}\n")
            print(f"  Aggiunto: {m3u8}")
        except Exception as e:
            print(f"  Errore per {title}: {e}")