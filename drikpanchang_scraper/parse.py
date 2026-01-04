import re
import logging
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from dateutil import parser as dateutil_parser
import pytz

logger = logging.getLogger(__name__)

RASHI_MAP = {
    'aries': 'Aries', 'taurus': 'Taurus', 'gemini': 'Gemini', 'cancer': 'Cancer',
    'leo': 'Leo', 'virgo': 'Virgo', 'libra': 'Libra', 'scorpio': 'Scorpio',
    'sagittarius': 'Sagittarius', 'capricorn': 'Capricorn', 'aquarius': 'Aquarius', 'pisces': 'Pisces',
}

NAKSHATRA_LIST = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashirsha', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Svati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
]

def normalize_datetime(raw_str: str, assume_tz: str = 'Asia/Kolkata') -> tuple:
    """
    Parse datetime string from DrikPanchang HTML and convert to UTC.

    Returns: (local_dt, tz_str, utc_dt)
    """
    try:
        local_dt = dateutil_parser.parse(raw_str, fuzzy=True)
        
        if local_dt.tzinfo is None:
            tz = pytz.timezone(assume_tz)
            local_dt = tz.localize(local_dt)
        
        utc_dt = local_dt.astimezone(pytz.UTC)
        return local_dt, local_dt.tzinfo.zone, utc_dt
    except Exception as e:
        logger.warning(f"Failed to parse datetime '{raw_str}': {e}")
        return None, None, None

def extract_event_rows_from_html(html: str, planet: str, endpoint_type: str) -> List[Dict]:
    """
    Extract event rows from DrikPanchang HTML using regex patterns.

    Handles patterns like:
      "Sun transits to Aries at 2024-03-20 18:00:00"
      "Moon enters Ashwini at 2024-01-11 04:30:00"
      "Jupiter transits to Leo pada 1 on 2024-05-15 12:00:00"
    """
    rows = []
    planet_name_upper = planet.capitalize()
    
    if endpoint_type == 'rashi':
        # Pattern for rashi transit
        rashi_pattern = r'(?:' + planet_name_upper + r')\s+(?:transits?|enters?)\s+(?:to\s+)?(\w+)\s+(?:on|at)\s+([^\n<]+)'
        matches = re.finditer(rashi_pattern, html, re.IGNORECASE)
        
        for match in matches:
            to_rashi = match.group(1).strip()
            event_dt_str = match.group(2).strip()
            
            to_rashi_norm = next((v for k, v in RASHI_MAP.items() if k in to_rashi.lower()), to_rashi)
            
            local_dt, tz_str, utc_dt = normalize_datetime(event_dt_str)
            
            if utc_dt:
                rows.append({
                    'planet': planet,
                    'endpoint_type': 'rashi',
                    'event_type': 'transit',
                    'from_sign': None,
                    'to_sign': to_rashi_norm,
                    'from_nakshatra': None,
                    'to_nakshatra': None,
                    'to_pada': None,
                    'event_local_dt': local_dt.isoformat() if local_dt else None,
                    'event_tz': tz_str or 'Asia/Kolkata',
                    'event_utc_dt': utc_dt.isoformat(),
                })
    
    elif endpoint_type == 'nakshatra':
        # Pattern for nakshatra transit
        nakshatra_pattern = r'(?:' + planet_name_upper + r')\s+(?:transits?|enters?)\s+(?:to\s+)?(' + '|'.join(NAKSHATRA_LIST) + r')\s+(?:on|at)\s+([^\n<]+)'
        matches = re.finditer(nakshatra_pattern, html, re.IGNORECASE)
        
        for match in matches:
            to_nakshatra = match.group(1).strip()
            event_dt_str = match.group(2).strip()
            
            local_dt, tz_str, utc_dt = normalize_datetime(event_dt_str)
            
            if utc_dt:
                rows.append({
                    'planet': planet,
                    'endpoint_type': 'nakshatra',
                    'event_type': 'transit',
                    'from_sign': None,
                    'to_sign': None,
                    'from_nakshatra': None,
                    'to_nakshatra': to_nakshatra,
                    'to_pada': None,
                    'event_local_dt': local_dt.isoformat() if local_dt else None,
                    'event_tz': tz_str or 'Asia/Kolkata',
                    'event_utc_dt': utc_dt.isoformat(),
                })
    
    elif endpoint_type == 'pada':
        # Pattern for pada transit: "Planet transits to <Nakshatra> pada <1-4>"
        pada_pattern = r'(?:' + planet_name_upper + r')\s+(?:transits?|enters?)\s+(?:to\s+)?(' + '|'.join(NAKSHATRA_LIST) + r')\s+pada\s+([1-4])\s+(?:on|at)\s+([^\n<]+)'
        matches = re.finditer(pada_pattern, html, re.IGNORECASE)
        
        for match in matches:
            to_nakshatra = match.group(1).strip()
            to_pada = int(match.group(2))
            event_dt_str = match.group(3).strip()
            
            local_dt, tz_str, utc_dt = normalize_datetime(event_dt_str)
            
            if utc_dt:
                rows.append({
                    'planet': planet,
                    'endpoint_type': 'pada',
                    'event_type': 'transit',
                    'from_sign': None,
                    'to_sign': None,
                    'from_nakshatra': None,
                    'to_nakshatra': to_nakshatra,
                    'to_pada': to_pada,
                    'event_local_dt': local_dt.isoformat() if local_dt else None,
                    'event_tz': tz_str or 'Asia/Kolkata',
                    'event_utc_dt': utc_dt.isoformat(),
                })
    
    return rows

# Parser functions for each planet + endpoint combination
def parse_planet(html: str, planet: str, endpoint_type: str, year: int) -> pd.DataFrame:
    """Generic parser for any planet + endpoint."""
    rows = extract_event_rows_from_html(html, planet, endpoint_type)
    df = pd.DataFrame(rows)
    df['year'] = year
    return df

# Convenience functions
def parse_sun_rashi(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'sun', 'rashi', year)

def parse_sun_nakshatra(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'sun', 'nakshatra', year)

def parse_moon_rashi(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'moon', 'rashi', year)

def parse_moon_nakshatra(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'moon', 'nakshatra', year)

def parse_mars_rashi(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'mars', 'rashi', year)

def parse_mars_nakshatra(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'mars', 'nakshatra', year)

def parse_mercury_rashi(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'mercury', 'rashi', year)

def parse_mercury_nakshatra(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'mercury', 'nakshatra', year)

def parse_jupiter_rashi(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'jupiter', 'rashi', year)

def parse_jupiter_nakshatra(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'jupiter', 'nakshatra', year)

def parse_venus_rashi(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'venus', 'rashi', year)

def parse_venus_nakshatra(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'venus', 'nakshatra', year)

def parse_saturn_rashi(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'saturn', 'rashi', year)

def parse_saturn_nakshatra(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'saturn', 'nakshatra', year)

def parse_rahu_rashi(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'rahu', 'rashi', year)

def parse_rahu_nakshatra(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'rahu', 'nakshatra', year)

def parse_rahu_pada(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'rahu', 'pada', year)

def parse_ketu_rashi(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'ketu', 'rashi', year)

def parse_ketu_nakshatra(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'ketu', 'nakshatra', year)

def parse_ketu_pada(html: str, year: int) -> pd.DataFrame:
    return parse_planet(html, 'ketu', 'pada', year)
