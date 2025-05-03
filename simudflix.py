from __future__ import annotations
import requests
import urllib.parse
import re
from typing import Literal
from dataclasses import dataclass
import os
from github import Github

@dataclass
class Title:
    id: int
    slug: str
    _type: Literal["movie", "tv"]

class StreamingCommunity:

    @dataclass
    class _Title:
        id: int
        name: str
        slug: str
        type_: Literal["movie", "tv"]
        __sc: StreamingCommunity

        def __init__(
            self,
            id: int,
            name: str,
            slug: str,
            type_: Literal["movie", "tv"],
            __sc: StreamingCommunity
        ):
            self.id = id
            self.name = name
            self.slug = slug
            self.type_ = type_
            self.__sc = __sc

        def get(self) -> StreamingCommunity._Movie:
            if (self.type_ == "movie"):
                return self.__get_movie()
            else:
                return self.__get_tv()

        def __get_movie(self) -> StreamingCommunity._Movie:
            url = f"{self.__sc.base_url}/titles/{self.id}-{self.slug}"
            inertia_version = StreamingCommunity._get_inertia_version(url)
            res = requests.get(url,
                headers={
                    "X-Inertia": "true",
                    "X-Inertia-Version": inertia_version
                }
            )

            props = res.json()["props"]
            title = props["title"]

            return StreamingCommunity._Movie(
                title["id"],
                title["name"],
                title["slug"],
                title["plot"],
                title["quality"],
                f"{props['scws_url']}/playlist/{props['title']['scws_id']}"
            )

        def __get_tv(self) -> StreamingCommunity._Tv:
            url = f"{self.__sc.base_url}/titles/{self.id}-{self.slug}"
            inertia_version = StreamingCommunity._get_inertia_version(url)
            res = requests.get(url,
                headers={
                    "X-Inertia": "true",
                    "X-Inertia-Version": inertia_version
                }
            )

            props = res.json()["props"]
            title = props["title"]

            seasons = []

            for s in title["seasons"]:
                season_url = f"{self.__sc.base_url}/titles/{self.id}-{self.slug}/stagione-{s['number']}"
                inertia_version = StreamingCommunity._get_inertia_version(season_url)
                res = requests.get(season_url,
                    headers={
                        "X-Inertia": "true",
                        "X-Inertia-Version": inertia_version
                    }
                )

                episodes = list(map(
                    lambda e: StreamingCommunity._Episode(
                        e["id"],
                        e["name"],
                        e["plot"],
                        f"{props['scws_url']}/playlist/{e['scws_id']}"
                    ),
                    res.json()["props"]["loadedSeason"]["episodes"]))

                seasons.append(StreamingCommunity._Season(
                    s["id"], s["number"], episodes
                ))

            return StreamingCommunity._Tv(
                title["id"],
                title["name"],
                title["slug"],
                title["plot"],
                title["quality"],
                seasons
            )

    @dataclass
    class _Movie:
        id: int
        name: str
        slug: str
        plot: str
        quality: str
        playlist_url: str

    @dataclass
    class _Tv:
        id: int
        name: str
        slug: str
        plot: str
        quality: str
        seasons: list[_Season]

    @dataclass
    class _Season:
        id: int
        number: int
        episodes: list[_Episode]

    @dataclass
    class _Episode:
        id: int
        name: str
        plot: str
        playlist_url: str

    base_url: str

    def __init__(self, base_url: str):
        self.base_url = base_url

    def search(self, query: str) -> list[_Title]:
        params = {"q": query}
        url = f"{self.base_url}/search?{urllib.parse.urlencode(params)}"
        inertia_version = self._get_inertia_version(url)
        res = requests.get(url,
            headers={
                "X-Inertia": "true",
                "X-Inertia-Version": inertia_version
            }
        )
        titles = res.json()['props']['titles']
        return list(map(
            lambda t: self._Title(t["id"], t["name"], t["slug"], t["type"], self),
            titles
        ))

    @staticmethod
    def _get_inertia_version(url: str) -> str | None:

        pattern = r"version&quot;:&quot;([a-f0-9]+)&quot;"

        res = requests.get(url)
        _match = re.search(pattern, res.text)
        if _match:
            return _match.group(1)
        else:
            raise LookupError(f"Given url ({url}) is not an Inertia application")

# Funzione per creare file m3u8
def create_m3u8_file(playlist_url: str, filename: str):
    m3u8_content = f"#EXTM3U\n#EXTINF:-1, {filename}\n{playlist_url}"
    with open(filename, "w") as m3u8_file:
        m3u8_file.write(m3u8_content)
    print(f"File {filename} creato con successo!")

# Funzione per caricare il file su GitHub
def upload_to_github(filename: str, repo_name: str, access_token: str):
    g = Github(access_token)
    repo = g.get_repo(repo_name)
    with open(filename, "r") as file:
        content = file.read()
    repo.create_file(f"streaming.m3u8", "Upload streaming.m3u8", content)
    print("File caricato su GitHub!")

# Creazione della sessione
sc = StreamingCommunity("https://streamingcommunity.spa")
titles = sc.search("John Wick")  # Cerca "John Wick" o qualsiasi altro titolo
movie = titles[0].get()  # Supponiamo che il primo risultato sia un film

# Crea il file M3U8
create_m3u8_file(movie.playlist_url, "streaming.m3u8")

# Carica il file su GitHub
upload_to_github("streaming.m3u8", "nome-repository", "access_token")  # Sostituisci con il tuo repository e token