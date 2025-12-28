# data_pipeline/planetary_data.py - Compute planetary positions with Skyfield

import pandas as pd
import numpy as np
from skyfield import api
from datetime import datetime, timedelta
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Planetary body codes (SPICE IDs used by Skyfield)
BODIES = {
    'sun': 10,
    'mercury': 199,
    'venus': 299,
    'mars': 499,
    'jupiter': 5,      # Jupiter barycenter
    'saturn': 6,       # Saturn barycenter
    'uranus': 7,       # Uranus barycenter
    'neptune': 8,      # Neptune barycenter
    'pluto': 9,        # Pluto barycenter
    'moon': 301,
}

def compute_planetary_positions(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Compute planetary positions using Skyfield
    
    Args:
        start_date: YYYY-MM-DD format
        end_date: YYYY-MM-DD format
    
    Returns:
        DataFrame with planetary positions or empty DataFrame if failed
    """
    logger.info(f"Computing planetary positions from {start_date} to {end_date}...")
    logger.info("Downloading ephemeris data (de421.bsp)...")
    
    try:
        # Load ephemeris and timescale
        # Note: cache parameter removed in Skyfield 1.46+
        ts = api.load.timescale()
        eph = api.load('de421.bsp')
        earth = eph['earth']
        sun = eph['sun']
        moon = eph['moon']
        
        logger.info("✓ Ephemeris loaded successfully")
        
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Generate daily timestamps
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        
        logger.info(f"Computing positions for {len(dates)} days...")
        
        # Create time objects - pass separate lists for year, month, day
        # Skyfield's ts.utc() expects: ts.utc(year, month, day, [hour, minute, second])
        years = [d.year for d in dates]
        months = [d.month for d in dates]
        days = [d.day for d in dates]
        times = ts.utc(years, months, days)
        
        logger.info(f"✓ Created time objects for {len(times)} dates")
        
        # Compute positions
        positions = []
        
        for i, (t, date) in enumerate(zip(times, dates)):
            if (i + 1) % 100 == 0:
                logger.info(f"  Processing day {i + 1}/{len(dates)}...")
            
            row = {'date': date}
            
            # Base: Earth position at time t
            earth_at_t = earth.at(t)
            
            # Sun position (geocentric apparent)
            sun_astrometric = earth_at_t.observe(sun).apparent()
            sun_lon, sun_lat, _ = sun_astrometric.ecliptic_latlon()
            row['sun_longitude'] = sun_lon.degrees
            row['sun_latitude'] = sun_lat.degrees
            row['sun_declination'] = sun_astrometric.radec()[1].degrees
            
            # Moon position (geocentric apparent)
            moon_astrometric = earth_at_t.observe(moon).apparent()
            moon_lon, moon_lat, _ = moon_astrometric.ecliptic_latlon()
            row['moon_longitude'] = moon_lon.degrees
            row['moon_latitude'] = moon_lat.degrees
            row['moon_declination'] = moon_astrometric.radec()[1].degrees
            
            # Moon phase (0-360 degrees): difference in ecliptic longitudes
            phase = (moon_lon.degrees - sun_lon.degrees) % 360.0
            row['moon_phase'] = phase
            
            # Other planets (geocentric apparent)
            planet_names = ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
            for planet_name in planet_names:
                try:
                    planet = eph[BODIES[planet_name]]
                    planet_astrometric = earth_at_t.observe(planet).apparent()
                    planet_lon, planet_lat, _ = planet_astrometric.ecliptic_latlon()
                    row[f'{planet_name}_longitude'] = planet_lon.degrees
                    row[f'{planet_name}_latitude'] = planet_lat.degrees
                    row[f'{planet_name}_declination'] = planet_astrometric.radec()[1].degrees
                except Exception as e:
                    logger.warning(f"Failed to compute {planet_name}: {e}")
                    row[f'{planet_name}_longitude'] = np.nan
                    row[f'{planet_name}_latitude'] = np.nan
                    row[f'{planet_name}_declination'] = np.nan
            
            positions.append(row)
        
        df = pd.DataFrame(positions)
        logger.info(f"✓ Computed {len(df)} records")
        
        return df
        
    except Exception as e:
        logger.error(f"✗ Failed to compute planetary data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def validate_planetary_data(df: pd.DataFrame) -> dict:
    """Validate planetary data quality"""
    if df.empty:
        return {'status': 'EMPTY', 'rows': 0}
    
    # Count columns
    longitude_cols = [col for col in df.columns if 'longitude' in col]
    
    stats = {
        'status': 'OK',
        'total_rows': len(df),
        'date_range': f"{df['date'].min().date()} to {df['date'].max().date()}",
        'missing_values': df.isnull().sum().sum(),
        'missing_pct': (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100) if len(df) > 0 else 0,
        'features': len(df.columns),
        'planets': len(longitude_cols),
    }
    
    return stats

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    START_DATE = (datetime.now() - timedelta(days=365*10)).strftime("%Y-%m-%d")
    
    logger.info(f"\n{'='*70}")
    df = compute_planetary_positions(START_DATE, END_DATE)
    stats = validate_planetary_data(df)
    
    logger.info(f"\nStats:")
    for key, val in stats.items():
        logger.info(f"  {key}: {val}")
    
    if not df.empty:
        logger.info(f"\nSample data:")
        logger.info(df.head(2))
