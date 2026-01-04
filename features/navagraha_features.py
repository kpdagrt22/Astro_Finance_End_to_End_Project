"""
Feature engineering for all 9 planets (Navagraha) gochar data.

Features include:
  1. Individual planet features (days_since, days_to, current_rashi/nakshatra/pada)
  2. Planet pair interactions (aspect angles, separations)
  3. Navagraha stability (how many planets transiting same rashi)
  4. Planetary cycles (retrograde periods, speed characteristics)
  5. Dasha-cycle alignment with planet positions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

PLANETS = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']

RASHI_ORDER = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

NAKSHATRA_ORDER = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashirsha', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Svati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
]

# Average transit times per planet (days per rashi)
TRANSIT_DURATION_DAYS = {
    'sun': 30,      # ~30 days per sign
    'moon': 2.25,   # ~2.25 days per sign
    'mars': 45,     # ~45 days per sign
    'mercury': 30,  # ~30 days per sign
    'jupiter': 365, # ~1 year per sign
    'venus': 30,    # ~30 days per sign
    'saturn': 900,  # ~2.5 years per sign
    'rahu': 1340,   # ~18 months per sign (18*30 days)
    'ketu': 1340,   # ~18 months per sign
}

class NavagrahaFeatureEngine:
    """Compute features from all 9 planets gochar data."""

    def __init__(self, events_df: pd.DataFrame):
        """
        Args:
            events_df: Merged events CSV with all planets
                Columns: [planet, endpoint_type, to_sign, to_nakshatra, to_pada, event_utc_dt, ...]
        """
        self.events_df = events_df.copy()
        self.events_df['event_utc_dt'] = pd.to_datetime(self.events_df['event_utc_dt'], utc=True)
        self.events_df = self.events_df.sort_values('event_utc_dt').reset_index(drop=True)

    def _get_current_state(
        self,
        planet: str,
        endpoint_type: str,
        as_of_date: datetime,
    ) -> Optional[str]:
        """Get current rashi/nakshatra/pada as of a given date."""
        mask = (self.events_df['planet'] == planet) & \
               (self.events_df['endpoint_type'] == endpoint_type) & \
               (self.events_df['event_utc_dt'] <= as_of_date)
        
        if mask.sum() == 0:
            return None
        
        latest = self.events_df[mask].iloc[-1]
        
        if endpoint_type == 'rashi':
            return latest['to_sign']
        elif endpoint_type == 'nakshatra':
            return latest['to_nakshatra']
        elif endpoint_type == 'pada':
            return latest['to_pada']

    def _days_since_transition(
        self,
        planet: str,
        endpoint_type: str,
        as_of_date: datetime,
    ) -> Optional[int]:
        """Days since last transition."""
        mask = (self.events_df['planet'] == planet) & \
               (self.events_df['endpoint_type'] == endpoint_type) & \
               (self.events_df['event_utc_dt'] <= as_of_date)
        
        if mask.sum() == 0:
            return None
        
        last_event_date = self.events_df[mask].iloc[-1]['event_utc_dt']
        delta = (as_of_date.replace(tzinfo=None) - last_event_date.replace(tzinfo=None)).days
        return max(0, delta)

    def _days_to_next_transition(
        self,
        planet: str,
        endpoint_type: str,
        as_of_date: datetime,
    ) -> Optional[int]:
        """Days until next transition."""
        mask = (self.events_df['planet'] == planet) & \
               (self.events_df['endpoint_type'] == endpoint_type) & \
               (self.events_df['event_utc_dt'] > as_of_date)
        
        if mask.sum() == 0:
            return None
        
        next_event_date = self.events_df[mask].iloc[0]['event_utc_dt']
        delta = (next_event_date.replace(tzinfo=None) - as_of_date.replace(tzinfo=None)).days
        return max(0, delta)

    def compute_individual_planet_features(self, observation_dates: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Compute individual features for each planet.

        Features per planet:
          - {planet}_current_rashi
          - {planet}_current_nakshatra
          - {planet}_current_pada
          - {planet}_rashi_days_since
          - {planet}_rashi_days_to
          - {planet}_nakshatra_days_since
          - {planet}_nakshatra_days_to
          - {planet}_pada_days_since (if pada data exists)
          - {planet}_pada_days_to
        """
        features = pd.DataFrame(index=observation_dates)

        for planet in PLANETS:
            # Rashi features
            col_rashi = f'{planet}_current_rashi'
            col_rashi_since = f'{planet}_rashi_days_since'
            col_rashi_to = f'{planet}_rashi_days_to'

            features[col_rashi] = observation_dates.map(
                lambda d: self._get_current_state(planet, 'rashi', pd.Timestamp(d))
            )
            features[col_rashi_since] = observation_dates.map(
                lambda d: self._days_since_transition(planet, 'rashi', pd.Timestamp(d))
            )
            features[col_rashi_to] = observation_dates.map(
                lambda d: self._days_to_next_transition(planet, 'rashi', pd.Timestamp(d))
            )

            # Nakshatra features
            col_naks = f'{planet}_current_nakshatra'
            col_naks_since = f'{planet}_nakshatra_days_since'
            col_naks_to = f'{planet}_nakshatra_days_to'

            features[col_naks] = observation_dates.map(
                lambda d: self._get_current_state(planet, 'nakshatra', pd.Timestamp(d))
            )
            features[col_naks_since] = observation_dates.map(
                lambda d: self._days_since_transition(planet, 'nakshatra', pd.Timestamp(d))
            )
            features[col_naks_to] = observation_dates.map(
                lambda d: self._days_to_next_transition(planet, 'nakshatra', pd.Timestamp(d))
            )

            # Pada features (for nodes primarily; other planets less detailed)
            col_pada = f'{planet}_current_pada'
            col_pada_since = f'{planet}_pada_days_since'
            col_pada_to = f'{planet}_pada_days_to'

            features[col_pada] = observation_dates.map(
                lambda d: self._get_current_state(planet, 'pada', pd.Timestamp(d))
            )
            features[col_pada_since] = observation_dates.map(
                lambda d: self._days_since_transition(planet, 'pada', pd.Timestamp(d))
            )
            features[col_pada_to] = observation_dates.map(
                lambda d: self._days_to_next_transition(planet, 'pada', pd.Timestamp(d))
            )

        return features

    def compute_navagraha_stability(self, observation_dates: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Compute Navagraha stability metrics.

        Stability features:
          - planets_in_same_rashi: count of planets in each rashi
          - rashi_occupancy_count: how many distinct rashis occupied
          - navagraha_strength: index based on planet conjunction/aspect strength
        """
        features = pd.DataFrame(index=observation_dates)

        # Compute occupancy by rashi
        rashi_counts = {}
        for rashi in RASHI_ORDER:
            rashi_counts[f'planets_in_{rashi.lower()}'] = 0

        for obs_date in observation_dates:
            occupied_rashis = {}
            
            for planet in PLANETS:
                current_rashi = self._get_current_state(planet, 'rashi', pd.Timestamp(obs_date))
                if current_rashi:
                    occupied_rashis[current_rashi] = occupied_rashis.get(current_rashi, 0) + 1
            
            for rashi, count in occupied_rashis.items():
                features.loc[obs_date, f'planets_in_{rashi.lower()}'] = count
            
            features.loc[obs_date, 'distinct_rashis_occupied'] = len(occupied_rashis)

        return features.fillna(0)

    def compute_planet_pair_interactions(self, observation_dates: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Compute interactions between all planet pairs.

        Interaction features:
          - {p1}_{p2}_rashi_separation: angular distance (0-12)
          - {p1}_{p2}_conjunction: boolean (same rashi)
          - {p1}_{p2}_aspect: coded aspect (opposition, square, trine, sextile, etc.)
        """
        features = pd.DataFrame(index=observation_dates)
        rashi_to_idx = {r: i for i, r in enumerate(RASHI_ORDER)}

        # Generate all planet pairs
        planet_pairs = [
            (PLANETS[i], PLANETS[j])
            for i in range(len(PLANETS))
            for j in range(i + 1, len(PLANETS))
        ]

        for p1, p2 in planet_pairs:
            col_sep = f'{p1}_{p2}_rashi_sep'
            col_conj = f'{p1}_{p2}_conjunction'
            col_aspect = f'{p1}_{p2}_aspect'

            def compute_separation(obs_date):
                r1 = self._get_current_state(p1, 'rashi', pd.Timestamp(obs_date))
                r2 = self._get_current_state(p2, 'rashi', pd.Timestamp(obs_date))

                if r1 and r2 and r1 in rashi_to_idx and r2 in rashi_to_idx:
                    sep = abs((rashi_to_idx[r2] - rashi_to_idx[r1]) % 12)
                    return sep
                return None

            def compute_aspect(obs_date):
                sep = compute_separation(obs_date)
                if sep is None:
                    return None
                
                if sep == 0:
                    return 'conjunction'
                elif sep == 3 or sep == 9:
                    return 'square'
                elif sep == 4 or sep == 8:
                    return 'trine'
                elif sep == 2 or sep == 10:
                    return 'sextile'
                elif sep == 6:
                    return 'opposition'
                else:
                    return 'minor'

            features[col_sep] = observation_dates.map(compute_separation)
            features[col_conj] = observation_dates.map(
                lambda d: compute_separation(d) == 0 if compute_separation(d) is not None else False
            )
            features[col_aspect] = observation_dates.map(compute_aspect)

        return features
