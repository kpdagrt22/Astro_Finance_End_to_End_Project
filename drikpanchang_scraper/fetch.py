import os
import logging
import time
import random
from pathlib import Path
from typing import Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

# Suppress SSL/security warnings
disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)

DRIKPANCHANG_BASE = "https://www.drikpanchang.com/planet/transit"

PLANETS = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']

PLANET_ENDPOINTS = {
    'sun': {
        'rashi': '/sun-transit.html',
        'nakshatra': '/sun-nakshatra-transit.html',
        'pada': '/sun-nakshatra-pada-transit.html',
    },
    'moon': {
        'rashi': '/moon-transit.html',
        'nakshatra': '/moon-nakshatra-transit.html',
        'pada': '/moon-nakshatra-pada-transit.html',
    },
    'mars': {
        'rashi': '/mars-transit.html',
        'nakshatra': '/mars-nakshatra-transit.html',
        'pada': '/mars-nakshatra-pada-transit.html',
    },
    'mercury': {
        'rashi': '/mercury-transit.html',
        'nakshatra': '/mercury-nakshatra-transit.html',
        'pada': '/mercury-nakshatra-pada-transit.html',
    },
    'jupiter': {
        'rashi': '/jupiter-transit.html',
        'nakshatra': '/jupiter-nakshatra-transit.html',
        'pada': '/jupiter-nakshatra-pada-transit.html',
    },
    'venus': {
        'rashi': '/venus-transit.html',
        'nakshatra': '/venus-nakshatra-transit.html',
        'pada': '/venus-nakshatra-pada-transit.html',
    },
    'saturn': {
        'rashi': '/saturn-transit.html',
        'nakshatra': '/saturn-nakshatra-transit.html',
        'pada': '/saturn-nakshatra-pada-transit.html',
    },
    'rahu': {
        'rashi': '/rahu-transit.html',
        'nakshatra': '/rahu-nakshatra-transit.html',
        'pada': '/rahu-nakshatra-pada-transit.html',
    },
    'ketu': {
        'rashi': '/ketu-transit.html',
        'nakshatra': '/ketu-nakshatra-transit.html',
        'pada': '/ketu-nakshatra-pada-transit.html',
    },
}

# User-Agent strings (rotate to avoid blocking)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

def get_cache_dir():
    """Return cache directory for raw HTML."""
    cache_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'drikpanchang'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def _get_random_user_agent():
    """Get a random user agent string."""
    return random.choice(USER_AGENTS)

def _create_session():
    """Create a session with retry strategy and proper headers."""
    session = requests.Session()
    
    # Retry strategy
    retry_strategy = Retry(
        total=5,                          # Increased retries
        backoff_factor=2,                 # Exponential backoff: 2, 4, 8, 16, 32 seconds
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Proper headers to avoid blocking
    session.headers.update({
        'User-Agent': _get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Referer': 'https://www.drikpanchang.com/',
    })
    
    return session

def fetch_year_html(
    year: int,
    planet: str,
    endpoint_type: str = 'rashi',
    location: str = 'New Delhi, India',
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Optional[str]:
    """
    Fetch HTML for a given year, planet, and endpoint type.

    Args:
        year: Calendar year (e.g., 2024)
        planet: One of 'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu'
        endpoint_type: One of 'rashi', 'nakshatra', 'pada'
        location: Location string (used for timezone context)
        use_cache: Use cached HTML if available
        force_refresh: Bypass cache and fetch fresh

    Returns:
        HTML string or None if fetch fails after retries
    """
    if planet not in PLANET_ENDPOINTS:
        raise ValueError(f"Unknown planet: {planet}. Choose from {list(PLANET_ENDPOINTS.keys())}")
    
    if endpoint_type not in PLANET_ENDPOINTS[planet]:
        raise ValueError(f"Unknown endpoint_type for {planet}: {endpoint_type}")

    cache_dir = get_cache_dir()
    cache_file = cache_dir / planet / endpoint_type / f"{year}.html"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    # Check cache
    if use_cache and not force_refresh and cache_file.exists():
        logger.debug(f"Cache hit: {cache_file}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()

    # Fetch from web
    url = f"{DRIKPANCHANG_BASE}{PLANET_ENDPOINTS[planet][endpoint_type]}"
    params = {'year': year}
    
    logger.info(f"Fetching {planet} {endpoint_type} for year {year}...")
    session = _create_session()
    
    try:
        # Add longer timeout and verify=False for SSL issues
        response = session.get(
            url,
            params=params,
            timeout=20,
            verify=False,
            allow_redirects=True
        )
        response.raise_for_status()
        html = response.text
        
        # Verify we got actual content (not an error page)
        if len(html) < 100:
            logger.warning(f"Received suspiciously short HTML ({len(html)} bytes) for {planet} {year}")
            return None
        
        # Cache to disk
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.debug(f"Cached: {cache_file}")
        time.sleep(1.5)  # Respectful rate limiting (1.5 seconds between requests)
        return html
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.warning(f"403 Forbidden for {planet} {endpoint_type} year {year}. Site may have anti-scraping protection.")
        else:
            logger.error(f"HTTP Error {e.response.status_code} for {url}")
        return None
    
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url} for year {year}: {e}")
        return None
    finally:
        session.close()

def fetch_all_planets_year(
    year: int,
    endpoint_types: List[str] = None,
    location: str = 'New Delhi, India',
    use_cache: bool = True,
) -> dict:
    """
    Convenience function: fetch all planets for a single year.

    Returns:
        {planet: {endpoint_type: html}}
    """
    if endpoint_types is None:
        endpoint_types = ['rashi', 'nakshatra', 'pada']
    
    results = {}
    
    for planet in PLANETS:
        results[planet] = {}
        for endpoint_type in endpoint_types:
            html = fetch_year_html(year, planet, endpoint_type, location, use_cache)
            if html:
                results[planet][endpoint_type] = html
    
    return results
