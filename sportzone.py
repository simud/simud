import cloudscraper
from bs4 import BeautifulSoup
import re
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Custom SSL Adapter to handle SSL issues
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers="DEFAULT@SECLEVEL=1")
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

# Initialize cloudscraper and requests session with custom SSL adapter
scraper = cloudscraper.create_scraper()
session = requests.Session()
session.mount('https://', SSLAdapter())

# URL to fetch the sportzone domain
giardiniblog_url = "https://www.giardiniblog.it/migliori-siti-streaming-calcio/"

# Default fallback base URL
default_base_url = "https://sportzone.help"

# Output M3U8 file
m3u8_file = "sportzone.m3u8"

# User-agent for both fetching and M3U8 headers
user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"

# Function to fetch page source with cloudscraper, requests, or selenium
def fetch_page(url, verify_ssl=True):
    print(f"Fetching page: {url} (SSL verification: {verify_ssl})")
    headers = {"User-Agent": user_agent}
    
    # Try cloudscraper first
    try:
        response = scraper.get(url, headers=headers)
        response.raise_for_status()
        print(f"Successfully fetched {url} with cloudscraper")
        return response.text
    except Exception as e:
        print(f"Cloudscraper failed for {url}: {e}")
    
    # Fallback to requests with custom SSL adapter
    try:
        response = session.get(url, headers=headers, timeout=10, verify=verify_ssl)
        response.raise_for_status()
        print(f"Successfully fetched {url} with requests")
        return response.text
    except Exception as e:
        print(f"Requests failed for {url}: {e}")
    
    # Fallback to selenium
    print(f"Attempting to fetch {url} with selenium...")
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"user-agent={user_agent}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        html = driver.page_source
        driver.quit()
        if html:
            print(f"Successfully fetched {url} with selenium")
            return html
        else:
            print(f"Selenium returned empty content for {url}")
            return None
    except Exception as e:
        print(f"Selenium failed for {url}: {e}")
        return None

# Function to extract the sportzone domain from giardiniblog
def get_sportzone_domain():
    print(f"Fetching sportzone domain from: {giardiniblog_url}")
    html = fetch_page(giardiniblog_url, verify_ssl=True)
    if not html:
        print("Retrying without SSL verification due to previous failure...")
        html = fetch_page(giardiniblog_url, verify_ssl=False)
    
    if not html:
        print(f"Failed to fetch {giardiniblog_url}. Using default domain: {default_base_url}")
        return default_base_url

    # Search for sportzone domain in <a> tags (href or text)
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.text.lower()
        if 'sportzone' in text or 'sportzone' in href.lower():
            domain_match = re.match(r'(https?://[^/]+)', href)
            if domain_match:
                domain = domain_match.group(1) + "/"
                print(f"Found sportzone domain: {domain}")
                return domain
    print(f"No sportzone domain found in {giardiniblog_url}. Using default domain: {default_base_url}")
    return default_base_url

# Function to extract categories and handle pagination
def get_categories(base_url):
    print("Fetching categories from main page...")
    html = fetch_page(base_url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    category_links = set()  # Use set to avoid duplicates

    # Find all category links (e.g., /category/Calcio, /category/FORMULA1/1)
    for a in soup.find_all('a', href=re.compile(r'(?:https?://sportzone\.[a-zA-Z0-9]+)?/category/[^/]+(?:/\d+)?')):
        href = a.get('href')
        # Handle both relative and absolute URLs
        if href.startswith('http'):
            full_url = href
        else:
            full_url = base_url + '/' + href.lstrip('/')
        category_links.add(full_url)
        print(f"Found category: {full_url}")

    # Check for pagination links (e.g., /category/Calcio/2, /category/FORMULA1/2)
    for a in soup.find_all('a', href=re.compile(r'(?:https?://sportzone\.[a-zA-Z0-9]+)?/category/[^/]+/\d+')):
        href = a.get('href')
        if href.startswith('http'):
            full_url = href
        else:
            full_url = base_url + '/' + href.lstrip('/')
        if full_url not in category_links:
            category_links.add(full_url)
            print(f"Found paginated category: {full_url}")

    return list(category_links)

# Function to extract event links from a category page
def get_event_links(category_url, base_url):
    print(f"Fetching events from category: {category_url}")
    html = fetch_page(category_url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    event_links = []
    # Find all event links
    for a in soup.find_all('a', href=re.compile(r'(?:https?://sportzone\.[a-zA-Z0-9]+)?/event/')):
        href = a.get('href')
        # Handle both relative and absolute URLs
        if href.startswith('http'):
            full_url = href
        else:
            full_url = base_url + '/' + href.lstrip('/')
        # Extract group-title (e.g., Calcio) and channel name (e.g., Como vs Inter HD1)
        li = a.find('li', class_='list-group-item')
        if li:
            category = li.find('span', class_='cat').text.strip() if li.find('span', class_='cat') else 'Unknown'
            title = li.find('span', class_='cat_item').text.strip() if li.find('span', class_='cat_item') else 'Unknown'
            event_links.append({
                'url': full_url,
                'group_title': category,
                'title': title
            })
            print(f"Found event: {title} ({full_url}) with group-title: {category}")

    # Check for pagination within the category
    pagination_links = []
    for a in soup.find_all('a', href=re.compile(r'(?:https?://sportzone\.[a-zA-Z0-9]+)?/category/[^/]+/\d+')):
        href = a.get('href')
        if href.startswith('http'):
            full_url = href
        else:
            full_url = base_url + '/' + href.lstrip('/')
        if full_url not in pagination_links and full_url.startswith(category_url.split('/page/')[0]):
            pagination_links.append(full_url)
            print(f"Found pagination link: {full_url}")

    # Fetch events from paginated pages
    for page_url in pagination_links:
        print(f"Fetching paginated category: {page_url}")
        html = fetch_page(page_url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=re.compile(r'(?:https?://sportzone\.[a-zA-Z0-9]+)?/event/')):
                href = a.get('href')
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = base_url + '/' + href.lstrip('/')
                li = a.find('li', class_='list-group-item')
                if li:
                    category = li.find('span', class_='cat').text.strip() if li.find('span', class_='cat') else 'Unknown'
                    title = li.find('span', class_='cat_item').text.strip() if li.find('span', class_='cat_item') else 'Unknown'
                    event_links.append({
                        'url': full_url,
                        'group_title': category,
                        'title': title
                    })
                    print(f"Found event (paginated): {title} ({full_url}) with group-title: {category}")

    return event_links

# Function to extract M3U8 stream and image from event page
def get_stream_and_image(event_url, base_url):
    print(f"Fetching stream and image from event page: {event_url}")
    html = fetch_page(event_url)
    if not html:
        return None, None

    soup = BeautifulSoup(html, 'html.parser')
    # Look for image in <img class="tist" src="...">
    image_tag = soup.find('img', class_='tist')
    image_url = None
    if image_tag and image_tag.get('src'):
        image_url = image_tag.get('src')
        # Convert relative URL to absolute
        if not image_url.startswith('http'):
            image_url = base_url + '/' + image_url.lstrip('/')
        print(f"Found image: {image_url}")

    # Look for iframe
    iframe = soup.find('iframe', src=True)
    if iframe:
        iframe_src = iframe.get('src')
        print(f"Found iframe: src={iframe_src}")
        # Check if iframe src is an M3U8 or another page
        if iframe_src.endswith('.m3u8'):
            return iframe_src, image_url
        else:
            # Ensure iframe_src is a full URL
            if not iframe_src.startswith('http'):
                iframe_src = base_url + '/' + iframe_src.lstrip('/')
            # Fetch the iframe page to find the M3U8 stream
            print(f"Fetching iframe content: {iframe_src}")
            iframe_html = fetch_page(iframe_src)
            if iframe_html:
                # Look for M3U8 in iframe content
                m3u8_match = re.search(r'https?://[^\s"]+\.m3u8', iframe_html)
                if m3u8_match:
                    stream_url = m3u8_match.group(0)
                    print(f"Found M3U8 stream: {stream_url}")
                    return stream_url, image_url
    else:
        # Look for M3U8 directly in the page
        m3u8_match = re.search(r'https?://[^\s"]+\.m3u8', html)
        if m3u8_match:
            stream_url = m3u8_match.group(0)
            print(f"Found M3U8 stream directly: {stream_url}")
            return stream_url, image_url

    print(f"No stream found for {event_url}")
    return None, image_url

# Function to deduplicate M3U8 playlist
def deduplicate_m3u8():
    print("Checking for duplicate channels in M3U8 playlist...")
    try:
        with open(m3u8_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Store unique channels based on tvg-logo, group-title, title, and stream
        channels = []
        seen = set()
        current_channel = {}
        current_lines = []
        header_lines = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#EXTM3U') or line.startswith('#EXTINF:-1 info canali'):
                header_lines.append(line + '\n')
                continue

            current_lines.append(line + '\n')
            if line.startswith('#EXTINF:'):
                # Extract tvg-logo, group-title, and title
                tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', line)
                group_title_match = re.search(r'group-title="([^"]*)"', line)
                title_match = re.search(r',(.+)$', line)
                current_channel['tvg-logo'] = tvg_logo_match.group(1) if tvg_logo_match else ''
                current_channel['group-title'] = group_title_match.group(1) if group_title_match else ''
                current_channel['title'] = title_match.group(1) if title_match else ''
            elif line.startswith('#EXTVLCOPT:'):
                # Collect headers
                if 'headers' not in current_channel:
                    current_channel['headers'] = []
                current_channel['headers'].append(line)
            elif not line.startswith('#'):
                # Stream URL
                current_channel['stream'] = line
                # Create a tuple for uniqueness check
                channel_key = (
                    current_channel['tvg-logo'],
                    current_channel['group-title'],
                    current_channel['title'],
                    current_channel['stream']
                )
                if channel_key not in seen:
                    seen.add(channel_key)
                    channels.append({
                        'lines': current_lines.copy(),
                        'key': channel_key
                    })
                else:
                    print(f"Removed duplicate channel: {current_channel['title']} (stream: {current_channel['stream']})")
                # Reset for next channel
                current_channel = {}
                current_lines = []

        # Write deduplicated playlist
        with open(m3u8_file, 'w', encoding='utf-8') as f:
            f.writelines(header_lines)
            for channel in channels:
                f.writelines(channel['lines'])
        
        print(f"Deduplication complete. {len(lines) - len(header_lines) - sum(len(c['lines']) for c in channels)} duplicate lines removed.")
        return True
    except Exception as e:
        print(f"Error during deduplication: {e}")
        return False

# Function to create M3U8 playlist with custom headers and tvg-logo
def create_m3u8_playlist(events, base_url):
    print("Creating M3U8 playlist...")
    with open(m3u8_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write("#EXTINF:-1 info canali\n")
        for event in events:
            stream_url, image_url = get_stream_and_image(event['url'], base_url)
            if stream_url:
                # Add tvg-logo if image_url exists, otherwise omit it
                tvg_logo = f' tvg-logo="{image_url}"' if image_url else ''
                f.write(f'#EXTINF:-1 group-title="{event["group_title"]}"{tvg_logo},{event["title"]}\n')
                f.write(f'#EXTVLCOPT:http-user-agent={user_agent}\n')
                f.write(f'#EXTVLCOPT:http-referrer={base_url}\n')
                f.write(f'#EXTVLCOPT:http-origin={base_url}\n')
                f.write(f'{stream_url}\n')
                print(f"Added to playlist: {event['title']} (stream: {stream_url}, image: {image_url})")
            else:
                print(f"Skipping {event['title']} (no stream found)")
            time.sleep(1)  # Add delay to avoid rate limiting

    # Deduplicate the playlist
    deduplicate_m3u8()

# Main execution
def main():
    # Step 0: Determine the sportzone domain
    base_url = get_sportzone_domain()
    print(f"Using base URL: {base_url}")

    # Step 1: Get all category pages
    categories = get_categories(base_url)
    if not categories:
        print("No categories found. Exiting.")
        return

    # Step 2: Get all event links from all categories
    all_events = []
    for category in categories:
        events = get_event_links(category, base_url)
        all_events.extend(events)

    if not all_events:
        print("No events found. Exiting.")
        return

    # Step 3: Create and deduplicate M3U8 playlist
    create_m3u8_playlist(all_events, base_url)
    print(f"M3U8 playlist saved to {m3u8_file}")

if __name__ == "__main__":
    main()
