from scuapi import API

sc = API("streamingcommunity.spa")

ids = {
    "Iron Man": 312,
    "Iron Man 2": 313,
    "Iron Man 3": 314,
    "The Avengers": 315,
    "Captain America": 316,
    "Thor": 317,
    "Guardians of the Galaxy": 320,
    "Doctor Strange": 322,
    "Black Panther": 325,
    "Avengers: Endgame": 328
}

m3u_entries = []

for title, id_ in ids.items():
    try:
        details = sc.load(str(id_))
        m3u8_url = details.get("m3u8_url")
        if m3u8_url:
            m3u_entries.append(f"#EXTINF:-1,{title}\n{m3u8_url}")
        else:
            print(f"Flusso M3U8 non trovato per {title}")
    except Exception as e:
        print(f"Errore per {title}: {e}")

with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    f.write("\n".join(m3u_entries))

print("File streaming.m3u8 creato.")