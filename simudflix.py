import requests
from bs4 import BeautifulSoup
import json
import re

class VixCloud:
    def __init__(self):
        self.base_url = "https://streamingcommunity.spa"
        self.headers = {
            'Accept': 'text/html, application/xhtml+xml',
            'Accept-Language': 'en-GB,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'streamingcommunity.spa',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Brave";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-GPC': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
        self.xsrf_token, self.session_cookie = self.fingerprint()

    def search(self, query):
        url = f"{self.base_url}/search?q={query}"
        headers_search = {
            'X-Inertia': 'true',
            'X-Inertia-Version': '9f1517b00147fb7ff43b935a25c2b654',
            'X-Requested-With': 'XMLHttpRequest',
            'X-XSRF-TOKEN': self.xsrf_token,
        }
        try:
            response = requests.get(url, headers={**self.headers, **headers_search})
            response.raise_for_status()
            return response.json()['props']['titles'][0]['id']
        except:
            return None

    def extract_video_info(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        script_tag = soup.find('script', string=lambda s: s and 'window.masterPlaylist =' in s)
        if script_tag:
            match = re.search(r'params:\s*({.*})', script_tag.string, re.DOTALL)
            if match:
                json_content = match.group(1).replace("'", '"').replace(',}', '}')
                try:
                    return json.loads(json_content)
                except:
                    return None
        return None

    def get_iframe_src(self, url):
        response = requests.get(url, headers=self.headers)
        return response.text if response.status_code == 200 else None

    def extract_iframe_src(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        iframe = soup.find('iframe', {'src': True})
        return iframe['src'] if iframe else None

    def send_api_request(self, start_id):
        url = f"{self.base_url}/iframe/{start_id}"
        headers = self.headers.copy()
        headers["Referer"] = f"{self.base_url}/watch/{start_id}"
        headers["Cookie"] = f"XSRF-TOKEN={self.xsrf_token}; streamingcommunity_session={self.session_cookie}"
        response = requests.get(url, headers=headers)
        return response.text if response.status_code == 200 else None

    def fingerprint(self):
        url = f"{self.base_url}/watch/6814"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.cookies.get("XSRF-TOKEN"), response.cookies.get("streamingcommunity_session")
        return None, None

    def construct_video_url(self, base_url, video_info):
        return f"{base_url}?token={video_info['token']}&token480p={video_info['token480p']}&token720p={video_info['token720p']}&token1080p={video_info['token1080p']}&expires={video_info['expires']}"

    def fetch_sources(self, tmdb_id):
        start_id = self.search(tmdb_id)
        if not start_id:
            return None
        response_data = self.send_api_request(start_id)
        iframe = self.extract_iframe_src(response_data)
        if not iframe:
            return None
        videoid = iframe.split('/embed/')[1].split('?')[0]
        response_html = self.get_iframe_src(iframe)
        stream_info = self.extract_video_info(response_html)
        if not stream_info:
            return None
        return self.construct_video_url(f'https://vixcloud.co/playlist/{videoid}', stream_info)


if __name__ == "__main__":
    marvel_titles = [
        "Iron Man", "The Avengers", "Captain America", "Thor",
        "Black Panther", "Doctor Strange", "Guardiani della Galassia",
        "Spider-Man", "Ant-Man", "Captain Marvel"
    ]

    scraper = VixCloud()
    with open("streaming.m3u8", "w", encoding="utf-8") as file:
        file.write("#EXTM3U\n")
        for title in marvel_titles:
            url = scraper.fetch_sources(title)
            if url:
                file.write(f"#EXTINF:-1,{title}\n{url}\n")
                print(f"Aggiunto: {title}")
            else:
                print(f"Fallito: {title}")