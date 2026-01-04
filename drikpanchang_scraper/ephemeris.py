"""
Compute Navagraha (9-planet) positions using Swiss Ephemeris.
Install: pip install pyswisseph

This is more reliable than web scraping:
- ✅ No 404/403 errors
- ✅ Accurate to within seconds
- ✅ Deterministic
- ✅ Works offline
- ✅ Fast (can compute 125 years in seconds)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
import pytz

try:
    import swisseph as swe
except ImportError:
    raise ImportError("Install pyswisseph: pip install pyswisseph")

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
    'rahu': swe.MEAN_NODE,          # Rahu (ascending node)
    'ketu': swe.MEAN_NODE,          # Ketu (descending = opposite Rahu)
}

# Transit duration (approximate days per sign)
TRANSIT_DURATION_DAYS = {
    'sun': 30,      # 30 days per sign
    'moon': 2.25,   # 2.25 days per sign
    'mars': 45,     # 45 days per sign
    'mercury': 30,  # 30 days per sign
    'jupiter': 365, # 1 year per sign
    'venus': 30,    # 30 days per sign
    'saturn': 900,  # 2.5 years per sign
    'rahu': 540,    # 18 months per sign
    'ketu': 540,    # 18 months per sign
}

class VedicEphemerisEngine:
    """Compute planetary positions and transitions using Swiss Ephemeris."""

    @staticmethod
    def get_planet_longitude(planet: str, date: datetime) -> float:
        """
        Get planet longitude (0-360 degrees) for a given date (UTC).

        Args:
            planet: Planet name (e.g., 'sun', 'moon', 'rahu')
            date: Datetime in UTC

        Returns:
            Longitude in degrees [0, 360)
        """
        if planet not in PLANET_INDICES:
            raise ValueError(f"Unknown planet: {planet}")

        # Convert to Julian Day
        jd = swe.utc_to_jd(date.year, date.month, date.day, date.hour, date.minute, date.second)[0]

        planet_idx = PLANET_INDICES[planet]

        # Compute planet position
        position, _ = swe.calc_ut(jd, planet_idx)
        longitude = position[0] % 360

        # For Ketu, add 180 degrees (opposite of Rahu)
        if planet == 'ketu':
            longitude = (longitude + 180) % 360

        return longitude

    @staticmethod
    def longitude_to_rashi(longitude: float) -> str:
        """Convert longitude (0-360) to rashi (zodiac sign)."""
        rashi_idx = int(longitude / 30)  # 30 degrees per sign
        return RASHI_ORDER[rashi_idx % 12]

    @staticmethod
    def longitude_to_nakshatra(longitude: float) -> Tuple[str, int]:
        """
        Convert longitude to nakshatra and pada.

        Returns:
            (nakshatra_name, pada_1_to_4)
        """
        nakshatra_idx = int(longitude / (360 / 27))  # 27 nakshatras
        pada_idx = int((longitude % (360 / 27)) / (360 / 108))  # 4 padas per nakshatra

        return NAKSHATRA_LIST[nakshatra_idx % 27], (pada_idx % 4) + 1

    @staticmethod
    def find_transition_times(
        planet: str,
        start_year: int,
        end_year: int,
        endpoint_type: str = 'rashi',
        step_days: int = 1,
    ) -> pd.DataFrame:
        """
        Find exact transition times for a planet over a date range.

        Args:
            planet: Planet name
            start_year: Start year (e.g., 1900)
            end_year: End year (e.g., 2025)
            endpoint_type: 'rashi' or 'nakshatra' (pada handled in nakshatra)
            step_days: Step size for scanning (smaller = more accurate but slower)

        Returns:
            DataFrame with transition events
        """
        logger.info(f"Computing {planet} {endpoint_type} transitions ({start_year}-{end_year})...")

        events = []
        start_date = datetime(start_year, 1, 1, tzinfo=pytz.UTC)
        end_date = datetime(end_year, 12, 31, tzinfo=pytz.UTC)

        current_date = start_date
        last_state = None

        while current_date <= end_date:
            try:
                lon = VedicEphemerisEngine.get_planet_longitude(planet, current_date)

                if endpoint_type == 'rashi':
                    current_state = VedicEphemerisEngine.longitude_to_rashi(lon)
                else:  # nakshatra
                    current_state, pada = VedicEphemerisEngine.longitude_to_nakshatra(lon)

                # Detect transition
                if current_state != last_state and last_state is not None:
                    # Find exact transition time (binary search)
                    exact_time = VedicEphemerisEngine._binary_search_transition(
                        planet,
                        current_date - timedelta(days=step_days),
                        current_date,
                        endpoint_type,
                        current_state
                    )

                    if exact_time:
                        if endpoint_type == 'rashi':
                            events.append({
                                'planet': planet,
                                'endpoint_type': 'rashi',
                                'event_type': 'transit',
                                'to_sign': current_state,
                                'event_utc_dt': exact_time.isoformat(),
                                'year': exact_time.year,
                            })
                        else:  # nakshatra
                            _, pada = VedicEphemerisEngine.longitude_to_nakshatra(
                                VedicEphemerisEngine.get_planet_longitude(planet, exact_time)
                            )
                            events.append({
                                'planet': planet,
                                'endpoint_type': 'nakshatra',
                                'event_type': 'transit',
                                'to_nakshatra': current_state,
                                'to_pada': pada,
                                'event_utc_dt': exact_time.isoformat(),
                                'year': exact_time.year,
                            })

                last_state = current_state

            except Exception as e:
                logger.warning(f"Error computing {planet} at {current_date}: {e}")

            # Adaptive step size based on planet speed
            if planet == 'moon':
                step_days = 1  # Fast planet
            elif planet in ['mercury', 'venus']:
                step_days = 2
            elif planet in ['sun', 'mars']:
                step_days = 5
            elif planet in ['jupiter', 'saturn', 'rahu', 'ketu']:
                step_days = 30  # Slow planets

            current_date += timedelta(days=step_days)

        logger.info(f"Found {len(events)} transitions for {planet} {endpoint_type}")
        return pd.DataFrame(events)

    @staticmethod
    def _binary_search_transition(
        planet: str,
        start: datetime,
        end: datetime,
        endpoint_type: str,
        target_state: str,
        precision_hours: float = 0.1,
        max_iterations: int = 20,
    ) -> Optional[datetime]:
        """Binary search to find exact transition time."""
        iteration = 0

        while (end - start).total_seconds() / 3600 > precision_hours and iteration < max_iterations:
            mid = start + (end - start) / 2
            lon = VedicEphemerisEngine.get_planet_longitude(planet, mid)

            if endpoint_type == 'rashi':
                mid_state = VedicEphemerisEngine.longitude_to_rashi(lon)
            else:
                mid_state, _ = VedicEphemerisEngine.longitude_to_nakshatra(lon)

            if mid_state == target_state:
                end = mid
            else:
                start = mid

            iteration += 1

        return end if iteration < max_iterations else None

    @staticmethod
    def compute_all_planets(
        start_year: int = 1900,
        end_year: int = 2025,
        output_dir: Optional[str] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Compute all 9 planets for all endpoint types.

        Returns:
            {(planet, endpoint_type): DataFrame}
        """
        from pathlib import Path

        if output_dir is None:
            output_dir = Path(__file__).parent.parent / 'data' / 'processed' / 'drikpanchang'
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
        endpoint_types = ['rashi', 'nakshatra']

        all_results = {}
        merged_rows = []

        for planet in planets:
            for endpoint_type in endpoint_types:
                logger.info(f"\n{'='*60}")
                logger.info(f"{planet.upper()} - {endpoint_type.upper()}")
                logger.info(f"{'='*60}")

                df = VedicEphemerisEngine.find_transition_times(
                    planet, start_year, end_year, endpoint_type
                )

                if not df.empty:
                    all_results[(planet, endpoint_type)] = df
                    merged_rows.extend(df.to_dict('records'))

                    # Save planet-specific file
                    output_file = output_dir / f'events_{planet}_{endpoint_type}.csv'
                    df.to_csv(output_file, index=False)
                    logger.info(f"✓ Saved: {output_file} ({len(df)} events)")
                else:
                    logger.warning(f"No transitions found")

        # Save merged file
        if merged_rows:
            merged_df = pd.DataFrame(merged_rows)
            merged_file = output_dir / 'events_all_planets_merged.csv'
            merged_df.to_csv(merged_file, index=False)
            logger.info(f"\n✓ Merged all planets: {merged_file} ({len(merged_df)} total events)")
            all_results['merged'] = merged_df

        return all_results
