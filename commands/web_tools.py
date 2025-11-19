# commands/web_tools.py
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse
from collections import deque
import re

from config import (
    ENABLE_LOGGING, LOG_FILE, MAX_WEB_SCRAPE_CONTENT_LENGTH, MAX_LINKS_TO_FOLLOW,
    GOOGLE_CSE_API_KEY, GOOGLE_CSE_ENGINE_ID
)

# --- Logger Setup ---
if ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(LOG_FILE, encoding='utf-8'),
                            logging.StreamHandler()
                        ])
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

def _sanitize_url(url: str) -> str:
    """Adds a schema to the URL if missing."""
    if not urlparse(url).scheme:
        url = "https://" + url
    return url.strip()

def browse_web_page(url: str) -> tuple[str, BeautifulSoup | None]:
    """
    Fetches and parses a web page.

    Args:
        url (str): The URL of the web page.

    Returns:
        A tuple containing:
        - str: The cleaned text content or an error message.
        - BeautifulSoup | None: The parsed soup object for link extraction, or None on error.
    """
    url = _sanitize_url(url)
    logger.info(f"Attempting to browse web page: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script_or_style in soup(['script', 'style', 'nav', 'footer', 'aside']):
            script_or_style.decompose()
            
        text_content = soup.get_text(separator='\n', strip=True)
        
        if len(text_content) > MAX_WEB_SCRAPE_CONTENT_LENGTH:
            logger.warning(f"Web content truncated from {len(text_content)} to {MAX_WEB_SCRAPE_CONTENT_LENGTH} chars.")
            text_content = text_content[:MAX_WEB_SCRAPE_CONTENT_LENGTH] + "..."
        
        logger.info(f"Successfully browsed {url}. Content length: {len(text_content)}")
        return text_content, soup

    except requests.exceptions.RequestException as e:
        logger.error(f"Error browsing web page {url}: {e}")
        return f"Error: Could not retrieve content from {url}. Reason: {e}", None
    except Exception as e:
        logger.error(f"An unexpected error occurred while browsing {url}: {e}")
        return f"An unexpected error occurred: {e}", None

def search_and_browse(query: str, num_results: int = 1, follow_links: bool = False) -> str:
    """
    Performs a Google search and browses the top results.
    """
    if not GOOGLE_CSE_API_KEY or "YOUR_GOOGLE_CSE_API_KEY" in GOOGLE_CSE_API_KEY:
        return "Error: Google CSE API Key is not set in config.py."
    if not GOOGLE_CSE_ENGINE_ID or "YOUR_GOOGLE_CSE_ENGINE_ID" in GOOGLE_CSE_ENGINE_ID:
        return "Error: Google CSE Engine ID is not set in config.py."

    search_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_CSE_API_KEY}&cx={GOOGLE_CSE_ENGINE_ID}&q={query}"
    logger.info(f"Performing Google Custom Search for: '{query}'")

    try:
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        search_results = response.json()

        if 'items' not in search_results:
            return f"No search results found for '{query}'."

        all_content = []
        browsed_urls = set()
        for item in search_results.get('items', [])[:num_results]:
            url = item.get('link')
            if not url or url in browsed_urls:
                continue

            title = item.get('title')
            snippet = item.get('snippet')
            logger.info(f"Browsing search result: {title} ({url})")
            
            content, soup = browse_web_page(url)
            browsed_urls.add(url)

            if soup:
                all_content.append(f"--- Content from: {title} ({url}) ---\nSnippet: {snippet}\n\n{content}\n")
                if follow_links:
                    # Efficiently use the existing soup object
                    internal_links = _extract_internal_links(url, soup, browsed_urls)
                    for link_to_follow in list(internal_links)[:MAX_LINKS_TO_FOLLOW]:
                        logger.info(f"Following internal link: {link_to_follow}")
                        followed_content, _ = browse_web_page(link_to_follow)
                        browsed_urls.add(link_to_follow)
                        if not followed_content.startswith("Error:"):
                            all_content.append(f"\n--- Content from Followed Link ({link_to_follow}) ---\n{followed_content}\n")
            else:
                all_content.append(f"\n--- Failed to retrieve content from {url} ---\n{content}\n")
    
    except requests.exceptions.RequestException as e:
        return f"Error: Could not perform web search. Reason: {e}"
    except Exception as e:
        return f"An unexpected error occurred during web search: {e}"

    if not all_content:
        return f"No content could be retrieved for query: '{query}'."

    return "\n".join(all_content)

def _extract_internal_links(base_url: str, soup: BeautifulSoup, browsed_urls: set) -> set:
    """Extracts a limited number of unique, internal links from a soup object."""
    internal_links = set()
    base_url_parsed = urlparse(base_url)
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        parsed_link = urlparse(full_url)
        
        if (parsed_link.netloc == base_url_parsed.netloc and
            parsed_link.scheme in ['http', 'https'] and
            not re.search(r'\.(pdf|zip|jpg|png|gif|mp4)$', parsed_link.path, re.IGNORECASE) and
            full_url not in browsed_urls and
            full_url not in internal_links):
            internal_links.add(full_url)
            if len(internal_links) >= MAX_LINKS_TO_FOLLOW * 2: # Get a few more to pick from
                break
    return internal_links
