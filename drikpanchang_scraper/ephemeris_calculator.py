"""
Alternative: Compute planetary positions using Swiss Ephemeris.
Install: pip install pyswisseph
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
import swisseph as swe
import pytz

logger = logging.getLogger(__name__)

RASHI_ORDER = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

NAKSHATRA_LIST = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashirsha', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Svati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
]

# Planet indices for Swiss Ephemeris
PLANET_INDICES = {
    'sun': swe.SUN,
    'moon': swe.MOON,
    'mars': swe.MARS,
    'mercury': swe.MERCURY,
    'jupiter': swe.JUPITER,
    'venus': swe.VENUS,
    'saturn': swe.SATURN,
    'rahu': swe.MEAN_NODE,      # Rahu (ascending node)
    'ketu': swe.MEAN_NODE + 1,  # Ketu (descending node, opposite Rahu)
}

def julian_day(date: datetime) -> float:
    """Convert datetime to Julian Day Number."""
    return swe.utc_to_jd(
        date.year, date.month, date.day,
        date.hour, date.minute, date.second
    )[0]

def get_planet_longitude(planet: str, date: datetime) -> float:
    """
    Get planet longitude (0-360 degrees) for a given date.
    
    Args:
        planet: Planet name (e.g., 'sun', 'moon', 'rahu')
        date: Datetime (assumed UTC)
    
    Returns:
        Longitude in degrees [0, 360)
    """
    if planet not in PLANET_INDICES:
        raise ValueError(f"Unknown planet: {planet}")
    
    jd = julian_day(date)
    planet_idx = PLANET_INDICES[planet]
    
    # Compute planet position
    position, _ = swe.calc_ut(jd, planet_idx)
    longitude = position[0] % 360
    
    return longitude

def longitude_to_rashi(longitude: float) -> str:
    """Convert longitude (0-360) to rashi (zodiac sign)."""
    rashi_idx = int(longitude / 30)  # 30 degrees per sign
    return RASHI_ORDER[rashi_idx % 12]

def longitude_to_nakshatra(longitude: float) -> Tuple[str, int]:
    """
    Convert longitude to nakshatra and pada.
    
    Returns:
        (nakshatra_name, pada_1_to_4)
    """
    nakshatra_idx = int(longitude / (360 / 27))  # 27 nakshatras in 360°
    pada_idx = int((longitude % (360 / 27)) / (360 / 108))  # 4 padas per nakshatra
    
    return NAKSHATRA_LIST[nakshatra_idx % 27], (pada_idx % 4) + 1

def find_rashi_transition_date(
    planet: str,
    target_rashi: str,
    start_date: datetime,
    max_days: int = 60,
) -> pd.DataFrame:
    """
    Find the exact date when a planet transits into a target rashi.
    
    Uses binary search for precision.
    """
    rashi_idx = RASHI_ORDER.index(target_rashi)
    target_lon_min = rashi_idx * 30
    target_lon_max = (rashi_idx + 1) * 30
    
    current_date = start_date
    events = []
    
    for day in range(max_days):
        current_date = start_date + timedelta(days=day)
        lon = get_planet_longitude(planet, current_date)
        current_rashi = longitude_to_rashi(lon)
        
        # Check if planet just entered target rashi
        if current_rashi == target_rashi:
            # Binary search for exact entry time
            exact_date = _binary_search_transition(planet, start_date + timedelta(days=day-1), start_date + timedelta(days=day+1), target_lon_min)
            
            if exact_date:
                events.append({
                    'planet': planet,
                    'endpoint_type': 'rashi',
                    'to_sign': target_rashi,
                    'event_utc_dt': exact_date.isoformat(),
                })
                break
    
    return pd.DataFrame(events)

def _binary_search_transition(planet: str, start: datetime, end: datetime, target_lon: float, precision_hours: int = 1) -> datetime:
    """Binary search to find exact transition time."""
    while (end - start).total_seconds() / 3600 > precision_hours:
        mid = start + (end - start) / 2
        lon = get_planet_longitude(planet, mid)
        
        if lon < target_lon:
            start = mid
        else:
            end = mid
    
    return end

def compute_ephemeris_data(
    planet: str,
    start_year: int,
    end_year: int,
    location: str = 'New Delhi, India',
) -> pd.DataFrame:
    """
    Compute planetary positions and transitions for a range of years.
    
    Returns:
        DataFrame with daily positions and detected transitions.
    """
    logger.info(f"Computing ephemeris data for {planet} ({start_year}-{end_year})")
    
    events = []
    start_date = datetime(start_year, 1, 1, tzinfo=pytz.UTC)
    end_date = datetime(end_year, 12, 31, tzinfo=pytz.UTC)
    
    current_date = start_date
    last_rashi = None
    last_nakshatra = None
    
    while current_date <= end_date:
        try:
            lon = get_planet_longitude(planet, current_date)
            rashi = longitude_to_rashi(lon)
            nakshatra, pada = longitude_to_nakshatra(lon)
            
            # Detect rashi transition
            if rashi != last_rashi and last_rashi is not None:
                events.append({
                    'planet': planet,
                    'endpoint_type': 'rashi',
                    'to_sign': rashi,
                    'event_utc_dt': current_date.isoformat(),
                })
            
            # Detect nakshatra transition
            if nakshatra != last_nakshatra and last_nakshatra is not None:
                events.append({
                    'planet': planet,
                    'endpoint_type': 'nakshatra',
                    'to_nakshatra': nakshatra,
                    'to_pada': pada,
                    'event_utc_dt': current_date.isoformat(),
                })
            
            last_rashi = rashi
            last_nakshatra = nakshatra
            
        except Exception as e:
            logger.warning(f"Error computing position for {planet} on {current_date}: {e}")
        
        # Increment by 1 day for fast planets, 5 days for slow planets
        if planet in ['moon']:
            current_date += timedelta(days=1)
        elif planet in ['mercury', 'venus']:
            current_date += timedelta(days=2)
        else:
            current_date += timedelta(days=5)
    
    return pd.DataFrame(events)
