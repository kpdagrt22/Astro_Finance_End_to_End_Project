"""
Navagraha computation using Skyfield (no C++ needed).
Install: pip install skyfield
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import pandas as pd
import pytz

try:
    from skyfield import api, wgs84
    from skyfield.data import hipparcos, mpc
except ImportError:
    raise ImportError("Install skyfield: pip install skyfield")

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

class SkyFieldEphemerisEngine:
    """Compute planetary positions using Skyfield."""

    # Skyfield planet names
    PLANET_NAMES = {
        'sun': 'sun',
        'moon': 'moon',
        'mars': 'mars',
        'mercury': 'mercury',
        'jupiter': 'jupiter',
        'venus': 'venus',
        'saturn': 'saturn',
    }

    # Node computed separately
    NODES = ['rahu', 'ketu']

    @staticmethod
    def _get_ephemeris():
        """Load ephemeris data (one-time download)."""
        logger.info("Loading ephemeris data...")
        ts = api.load.timescale()
        eph = api.load('de421.bsp')  # NASA JPL ephemeris
        return ts, eph

    @staticmethod
    def get_planet_longitude(planet: str, date: datetime) -> float:
        """
        Get planet ecliptic longitude (0-360 degrees).

        Args:
            planet: Planet name
            date: UTC datetime

        Returns:
            Longitude in degrees [0, 360)
        """
        from skyfield.api import load, wgs84
        from skyfield.constants import GM_SUN_Pitjeva

        ts, eph = SkyFieldEphemerisEngine._get_ephemeris()

        # Create observer at Earth center
        earth = eph['earth']
        sun = eph['sun']

        # Create time
        t = ts.utc(date.year, date.month, date.day, date.hour, date.minute, date.second)

        if planet == 'sun':
            # Sun from Earth
            astrometric = earth.at(t).observe(sun).apparent()
        elif planet == 'moon':
            # Moon from Earth
            moon = eph['moon']
            astrometric = earth.at(t).observe(moon).apparent()
        elif planet in SkyFieldEphemerisEngine.PLANET_NAMES:
            # Other planets
            planet_obj = eph[SkyFieldEphemerisEngine.PLANET_NAMES[planet]]
            astrometric = earth.at(t).observe(planet_obj).apparent()
        else:
            raise ValueError(f"Unknown planet: {planet}")

        # Get ecliptic longitude
        ecliptic_lon, ecliptic_lat = astrometric.apparent_equatorial_to_ecliptic().lonlat
        longitude = ecliptic_lon.degrees % 360

        # For Ketu, add 180 degrees
        if planet == 'ketu':
            longitude = (longitude + 180) % 360

        return longitude

    @staticmethod
    def longitude_to_rashi(longitude: float) -> str:
        """Convert longitude to rashi."""
        rashi_idx = int(longitude / 30)
        return RASHI_ORDER[rashi_idx % 12]

    @staticmethod
    def longitude_to_nakshatra(longitude: float) -> Tuple[str, int]:
        """Convert longitude to nakshatra and pada."""
        nakshatra_idx = int(longitude / (360 / 27))
        pada_idx = int((longitude % (360 / 27)) / (360 / 108))
        return NAKSHATRA_LIST[nakshatra_idx % 27], (pada_idx % 4) + 1

    @staticmethod
    def find_transition_times(
        planet: str,
        start_year: int,
        end_year: int,
        endpoint_type: str = 'rashi',
        step_days: int = 1,
    ) -> pd.DataFrame:
        """Find transition times for a planet."""
        logger.info(f"Computing {planet} {endpoint_type} transitions ({start_year}-{end_year})...")

        events = []
        start_date = datetime(start_year, 1, 1, tzinfo=pytz.UTC)
        end_date = datetime(end_year, 12, 31, tzinfo=pytz.UTC)

        current_date = start_date
        last_state = None

        while current_date <= end_date:
            try:
                lon = SkyFieldEphemerisEngine.get_planet_longitude(planet, current_date)

                if endpoint_type == 'rashi':
                    current_state = SkyFieldEphemerisEngine.longitude_to_rashi(lon)
                else:  # nakshatra
                    current_state, pada = SkyFieldEphemerisEngine.longitude_to_nakshatra(lon)

                # Detect transition
                if current_state != last_state and last_state is not None:
                    exact_time = SkyFieldEphemerisEngine._binary_search_transition(
                        planet, current_date - timedelta(days=step_days), current_date, endpoint_type, current_state
                    )

                    if exact_time:
                        if endpoint_type == 'rashi':
                            events.append({
                                'planet': planet,
                                'endpoint_type': 'rashi',
                                'to_sign': current_state,
                                'event_utc_dt': exact_time.isoformat(),
                                'year': exact_time.year,
                            })
                        else:  # nakshatra
                            _, pada = SkyFieldEphemerisEngine.longitude_to_nakshatra(
                                SkyFieldEphemerisEngine.get_planet_longitude(planet, exact_time)
                            )
                            events.append({
                                'planet': planet,
                                'endpoint_type': 'nakshatra',
                                'to_nakshatra': current_state,
                                'to_pada': pada,
                                'event_utc_dt': exact_time.isoformat(),
                                'year': exact_time.year,
                            })

                last_state = current_state

            except Exception as e:
                logger.warning(f"Error at {current_date}: {e}")

            # Adaptive step
            if planet == 'moon':
                step_days = 1
            elif planet in ['mercury', 'venus']:
                step_days = 2
            elif planet in ['sun', 'mars']:
                step_days = 5
            else:
                step_days = 30

            current_date += timedelta(days=step_days)

        logger.info(f"Found {len(events)} transitions")
        return pd.DataFrame(events)

    @staticmethod
    def _binary_search_transition(planet, start, end, endpoint_type, target_state, precision_hours=0.1):
        """Binary search for exact transition time."""
        iteration = 0
        max_iterations = 20

        while (end - start).total_seconds() / 3600 > precision_hours and iteration < max_iterations:
            mid = start + (end - start) / 2
            lon = SkyFieldEphemerisEngine.get_planet_longitude(planet, mid)

            if endpoint_type == 'rashi':
                mid_state = SkyFieldEphemerisEngine.longitude_to_rashi(lon)
            else:
                mid_state, _ = SkyFieldEphemerisEngine.longitude_to_nakshatra(lon)

            if mid_state == target_state:
                end = mid
            else:
                start = mid

            iteration += 1

        return end if iteration < max_iterations else None

    @staticmethod
    def compute_all_planets(start_year=1900, end_year=2025, output_dir=None):
        """Compute all 9 planets."""
        from pathlib import Path

        if output_dir is None:
            output_dir = Path(__file__).parent.parent / 'data' / 'processed' / 'drikpanchang'
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        planets = list(SkyFieldEphemerisEngine.PLANET_NAMES.keys()) + SkyFieldEphemerisEngine.NODES
        endpoint_types = ['rashi', 'nakshatra']

        all_results = {}
        merged_rows = []

        for planet in planets:
            for endpoint_type in endpoint_types:
                logger.info(f"\n{'='*60}")
                logger.info(f"{planet.upper()} - {endpoint_type.upper()}")
                logger.info(f"{'='*60}")

                try:
                    df = SkyFieldEphemerisEngine.find_transition_times(
                        planet, start_year, end_year, endpoint_type
                    )

                    if not df.empty:
                        all_results[(planet, endpoint_type)] = df
                        merged_rows.extend(df.to_dict('records'))

                        output_file = output_dir / f'events_{planet}_{endpoint_type}.csv'
                        df.to_csv(output_file, index=False)
                        logger.info(f"✓ Saved: {output_file} ({len(df)} events)")
                except Exception as e:
                    logger.error(f"Failed to compute {planet}: {e}")

        # Merge
        if merged_rows:
            merged_df = pd.DataFrame(merged_rows)
            merged_file = output_dir / 'events_all_planets_merged.csv'
            merged_df.to_csv(merged_file, index=False)
            logger.info(f"\n✓ Merged: {merged_file} ({len(merged_df)} total events)")
            all_results['merged'] = merged_df

        return all_results
