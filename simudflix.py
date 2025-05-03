from __future__ import annotations
import requests
import urllib.parse
import re
from typing import Literal
from dataclasses import dataclass

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
        params = { "q": query }
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

    def generate_m3u8(self, titles: list[_Title]) -> None:
        with open("streaming.m3u8", "w") as file:
            file.write("#EXTM3U\n")
            for title in titles:
                movie = title.get()
                file.write(f"#EXTINF:-1,{movie.name}\n")
                file.write(f"{movie.playlist_url}\n")

# Impostazione dell'oggetto StreamingCommunity per usare il dominio .spa
sc = StreamingCommunity("https://streamingcommunity.spa")

# Ricerca di un film
titles = sc.search("john wick")

# Generazione del file m3u8
sc.generate_m3u8(titles)