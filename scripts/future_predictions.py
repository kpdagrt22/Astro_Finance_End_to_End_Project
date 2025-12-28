# scripts/planetary_data.py - FIXED WITH GLOBAL LOADER

import pandas as pd
import numpy as np
from skyfield.api import Loader
from datetime import datetime, timedelta
from pathlib import Path
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'

# Ensure directories exist
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# Create GLOBAL Skyfield loader pointing ONLY to our data/raw folder
# This prevents any downloads
load = Loader(str(DATA_RAW), expire=False)

# Disable automatic downloads
os.environ['SKYFIELD_DOWNLOAD'] = '0'


def compute_planetary_positions(start_date, end_date):
    """
    Compute planetary positions for date range
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        DataFrame with planetary positions
    """
    
    logger.info(f"Computing planetary positions from {start_date} to {end_date}...")
    
    # Check if BSP file exists
    bsp_file = DATA_RAW / 'de421.bsp'
    if not bsp_file.exists():
        logger.error(f"❌ BSP file not found: {bsp_file}")
        logger.info(f"💡 Download from: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de421.bsp")
        logger.info(f"💡 Save to: {bsp_file}")
        raise FileNotFoundError(f"BSP file not found at {bsp_file}")
    
    logger.info(f"✓ Using local BSP file: {bsp_file}")
    
    # Load ephemeris from LOCAL file (will NOT download)
    try:
        eph = load('de421.bsp')
        logger.info("✓ Ephemeris loaded from local file (no download)")
    except Exception as e:
        logger.error(f"❌ Error loading ephemeris: {e}")
        raise
    
    # Create timescale (might download tiny timescale files first time only)
    try:
        ts = load.timescale()
    except Exception as e:
        logger.warning(f"⚠️  Timescale load issue: {e}")
        # Fallback: use built-in
        from skyfield.api import load as default_load
        ts = default_load.timescale(builtin=True)
    
    # Generate date range
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    dates = pd.date_range(start=start, end=end, freq='D')
    
    logger.info(f"✓ Processing {len(dates)} days...")
    
    # Planet codes
    planets = {
        'sun': 10,
        'moon': 301,
        'mercury': 1,
        'venus': 2,
        'mars': 4,
        'jupiter': 5,
        'saturn': 6,
        'uranus': 7,
        'neptune': 8,
        'pluto': 9
    }
    
    # Earth
    earth = eph[399]
    
    # Compute positions
    data = []
    
    for date in dates:
        t = ts.utc(date.year, date.month, date.day)
        
        row = {'date': date}
        
        # Get positions for each planet
        for planet_name, planet_code in planets.items():
            try:
                planet = eph[planet_code]
                
                # Position relative to Earth
                astrometric = earth.at(t).observe(planet)
                ra, dec, distance = astrometric.radec()
                
                # Ecliptic longitude (approximate)
                lon = ra.degrees
                
                row[f'{planet_name}_longitude'] = lon
                row[f'{planet_name}_distance'] = distance.au
                
            except Exception as e:
                logger.warning(f"Could not compute {planet_name}: {e}")
                row[f'{planet_name}_longitude'] = np.nan
                row[f'{planet_name}_distance'] = np.nan
        
        data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Calculate velocities (rate of change)
    for planet_name in planets.keys():
        lon_col = f'{planet_name}_longitude'
        if lon_col in df.columns:
            df[f'{planet_name}_velocity'] = df[lon_col].diff()
    
    logger.info(f"✓ Computed positions for {len(df)} days")
    
    return df


def save_planetary_data(df, filename='planetary_positions.csv'):
    """Save planetary data to processed folder"""
    output_path = DATA_PROCESSED / filename
    df.to_csv(output_path, index=False)
    logger.info(f"✓ Saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🌙 ASTRO FINANCE ML - PLANETARY DATA GENERATOR")
    logger.info("=" * 60)
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info(f"Data Folder: {DATA_RAW}")
    logger.info(f"Output: {DATA_PROCESSED}")
    logger.info("")
    
    # Test: Compute last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        df = compute_planetary_positions(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        print("\n📊 SAMPLE DATA (Last 5 Days):")
        print("=" * 80)
        print(df.tail(5)[['date', 'sun_longitude', 'moon_longitude', 'saturn_longitude']].to_string(index=False))
        
        # Save
        output_path = save_planetary_data(df)
        
        print(f"\n✅ SUCCESS!")
        print(f"   Data saved to: {output_path}")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {len(df.columns)}")
        
    except FileNotFoundError as e:
        logger.error(f"\n❌ {e}")
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
