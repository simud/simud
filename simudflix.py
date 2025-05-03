from scuapi import API

# Inizializza l'API con il dominio di StreamingCommunity
sc = API('StreamingCommunity.spa')  # Usa il dominio corretto (StreamingCommunity.spa o altro)

# Lista dei film da scegliere (modifica con i tuoi film preferiti)
movies = [
    "Thunderbolts",
    "Guardians of the Galaxy Vol. 3",
    "Spider-Man: No Way Home",
    "Black Panther: Wakanda Forever",
    "Avengers: Endgame",
    "Doctor Strange in the Multiverse of Madness",
    "Iron Man 3",
    "Captain America: Civil War",
    "Thor: Ragnarok",
    "Ant-Man and The Wasp"
]

# Per ogni film nella lista
for movie in movies:
    # Ricerca del film
    results = sc.search(movie)
    print(f"Risultati per '{movie}': {results}")
    
    # Prendi l'ID del film dalla ricerca
    movie_id = results[movie]["id"]
    
    # Ottieni i link m3u per il film
    m3u_link = sc.get_links(movie_id, get_m3u=True)
    
    # Crea un file m3u8 per ogni film
    with open(f'{movie.replace(" ", "_")}.m3u8', 'w') as f:
        f.write(m3u_link[1])  # m3u_link[1] contiene l'URL m3u8
        print(f"Flusso m3u8 per '{movie}' scritto in {movie.replace(' ', '_')}.m3u8")

print("Tutti i film sono stati elaborati.")