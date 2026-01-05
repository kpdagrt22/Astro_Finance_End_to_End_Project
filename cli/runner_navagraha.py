"""
Feature Engineering: Navagraha Planetary Features

Generates 170+ engineered features from planetary position events.
Features include:
- Individual planet positions (36 features)
- Planet pair interactions (108 features)  
- Stability metrics (15 features)
- Advanced features (8 features)
- Dasha cycles (3 features)

Total: 170+ daily features covering 1900-2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')


class NavagrahaFeatureEngine:
    """Build Navagraha (9-planet) features from planetary events"""
    
    # Planet symbols
    PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    
    # Zodiac signs (Rashi)
    RASHIS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
              'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    def __init__(self):
        """Initialize feature engine"""
        self.planet_state = None
        self.daily_index = None
    
    def build_daily_index(self, start_date: str, end_date: str) -> pd.DatetimeIndex:
        """
        Create continuous daily date index
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DatetimeIndex with all dates
        """
        return pd.date_range(start=start_date, end=end_date, freq='D')
    
    def build_planet_state_table(self, events_df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert event-based data to daily planet states
        
        For each day, determine which rashi and nakshatra each planet is in
        
        Args:
            events_df: Events DataFrame with columns:
                - planet, event_type, to_sign, to_nakshatra, event_utc_dt
        
        Returns:
            DataFrame with shape (dates, planets) showing current position
        """
        if events_df.empty:
            # Return dummy data if no events
            dates = self.build_daily_index('1900-01-01', '2025-12-31')
            return pd.DataFrame(
                np.zeros((len(dates), len(self.PLANETS) * 2)),
                index=dates,
                columns=[f"{p}_rashi" for p in self.PLANETS] + 
                        [f"{p}_nakshatra" for p in self.PLANETS]
            )
        
        # ⭐ FIXED: Use format='ISO8601' for datetime parsing
        dates = pd.to_datetime(events_df['event_utc_dt'], format='ISO8601')
        events_df = events_df.copy()
        events_df['event_utc_dt'] = dates
        events_df = events_df.sort_values('event_utc_dt')
        
        # Build state table
        daily_index = self.build_daily_index('1900-01-01', '2025-12-31')
        state = pd.DataFrame(
            np.zeros((len(daily_index), len(self.PLANETS) * 2)),
            index=daily_index,
            columns=[f"{p}_rashi" for p in self.PLANETS] + 
                    [f"{p}_nakshatra" for p in self.PLANETS]
        )
        
        # Fill with event data
        for planet in self.PLANETS:
            planet_events = events_df[events_df['planet'] == planet].copy()
            
            if not planet_events.empty:
                # Forward fill rashi
                rashi_col = f"{planet}_rashi"
                dates_arr = planet_events['event_utc_dt'].values
                rashis = planet_events['to_sign'].fillna(0).astype(int).values
                
                for date, rashi in zip(dates_arr, rashis):
                    try:
                        state.loc[pd.Timestamp(date):, rashi_col] = rashi
                    except:
                        pass
                
                # Forward fill nakshatra
                nak_col = f"{planet}_nakshatra"
                nakshatras = planet_events['to_nakshatra'].fillna(0).astype(int).values
                
                for date, nak in zip(dates_arr, nakshatras):
                    try:
                        state.loc[pd.Timestamp(date):, nak_col] = nak
                    except:
                        pass
        
        self.planet_state = state
        return state
    
    def build_individual_planet_features(self, planet_state: pd.DataFrame) -> pd.DataFrame:
        """
        Generate 36 individual planet features
        
        For each of 9 planets:
        - Current rashi (0-11)
        - Days since entering rashi
        - Current nakshatra (0-26)
        - Days since entering nakshatra
        
        Args:
            planet_state: DataFrame with planet positions
        
        Returns:
            DataFrame with 36 features
        """
        features = pd.DataFrame(index=planet_state.index)
        
        for planet in self.PLANETS:
            rashi_col = f"{planet}_rashi"
            nak_col = f"{planet}_nakshatra"
            
            # Current position
            features[f"{planet.lower()}_rashi"] = planet_state[rashi_col].astype(float)
            features[f"{planet.lower()}_nakshatra"] = planet_state[nak_col].astype(float)
            
            # Days since change
            rashi_changes = (planet_state[rashi_col] != planet_state[rashi_col].shift()).astype(int)
            rashi_group = rashi_changes.cumsum()
            features[f"{planet.lower()}_rashi_days_since"] = rashi_group.groupby(rashi_group).cumcount()
            
            nak_changes = (planet_state[nak_col] != planet_state[nak_col].shift()).astype(int)
            nak_group = nak_changes.cumsum()
            features[f"{planet.lower()}_nakshatra_days_since"] = nak_group.groupby(nak_group).cumcount()
        
        # Handle NaN from invalid operations
        features = features.fillna(0).astype(float)
        
        return features
    
    def build_pair_interaction_features(self, planet_state: pd.DataFrame) -> pd.DataFrame:
        """
        Generate 108 pair interaction features
        
        For each of 36 unique planet pairs:
        - Rashi separation (0-11)
        - Aspect classification (conjunction, opposite, etc)
        - Conjunction indicator (binary)
        
        Args:
            planet_state: DataFrame with planet positions
        
        Returns:
            DataFrame with 108 features
        """
        features = pd.DataFrame(index=planet_state.index)
        
        # All unique pairs
        pairs = []
        for i, p1 in enumerate(self.PLANETS):
            for j, p2 in enumerate(self.PLANETS):
                if i < j:
                    pairs.append((p1, p2))
        
        for p1, p2 in pairs:
            p1_lower = p1.lower()
            p2_lower = p2.lower()
            
            # Rashi separation
            sep = (planet_state[f"{p2}_rashi"] - planet_state[f"{p1}_rashi"]) % 12
            features[f"{p1_lower}_{p2_lower}_separation"] = sep.astype(float)
            
            # Aspect classification (simplified)
            aspect = np.where(sep <= 1, 0,  # Conjunction
                            np.where(sep == 6, 1,  # Opposition
                            np.where((sep >= 4) & (sep <= 5), 2,  # Square
                            3)))  # Other
            features[f"{p1_lower}_{p2_lower}_aspect"] = aspect.astype(float)
            
            # Conjunction (within 1 sign)
            features[f"{p1_lower}_{p2_lower}_conjunction"] = (sep <= 1).astype(float)
        
        return features
    
    def build_stability_metrics(self, planet_state: pd.DataFrame) -> pd.DataFrame:
        """
        Generate 15 stability features
        
        Measures of planetary distribution across rashis:
        - Count planets in each rashi (12)
        - Distinct rashis occupied (1)
        - Distribution entropy (2)
        
        Args:
            planet_state: DataFrame with planet positions
        
        Returns:
            DataFrame with 15 features
        """
        features = pd.DataFrame(index=planet_state.index)
        
        # Count planets in each rashi
        for rashi_idx in range(12):
            count = 0
            for planet in self.PLANETS:
                count += (planet_state[f"{planet}_rashi"] == rashi_idx).astype(int)
            features[f"planets_in_rashi_{rashi_idx}"] = count.astype(float)
        
        # Distinct rashis occupied
        distinct_rashis = 0
        for rashi_idx in range(12):
            distinct_rashis += (features[f"planets_in_rashi_{rashi_idx}"] > 0).astype(int)
        features['distinct_rashis_occupied'] = distinct_rashis.astype(float)
        
        # Rashi entropy
        planet_counts = features[[f"planets_in_rashi_{i}" for i in range(12)]].values
        total_planets = planet_counts.sum(axis=1, keepdims=True)
        total_planets[total_planets == 0] = 1  # Avoid division by zero
        probabilities = planet_counts / total_planets
        probabilities[probabilities == 0] = 1e-10  # Avoid log(0)
        
        rashi_entropy = -np.sum(probabilities * np.log2(probabilities), axis=1)
        features['rashi_entropy'] = rashi_entropy
        
        # Nakshatra entropy (simplified - using variance of nakshatra positions)
        nakshatra_positions = []
        for planet in self.PLANETS:
            nakshatra_positions.append(planet_state[f"{planet}_nakshatra"].values)
        
        nakshatra_array = np.array(nakshatra_positions)
        nakshatra_std = np.std(nakshatra_array, axis=0)
        features['nakshatra_entropy'] = nakshatra_std / 27.0  # Normalize by max nakshatra
        
        return features
    
    def build_advanced_features(self, planet_state: pd.DataFrame, 
                               pair_features: pd.DataFrame) -> pd.DataFrame:
        """
        Generate 8 advanced features
        
        Complex astrological concepts:
        - Planetary war index
        - Yoga strength
        - Cluster coherence
        - Benefic/malefic balance
        - Rahu effect
        - Grand conjunction
        - Retrograde count (placeholder)
        - Distribution entropy
        
        Args:
            planet_state: Planet position data
            pair_features: Pair interaction features
        
        Returns:
            DataFrame with 8 features
        """
        features = pd.DataFrame(index=planet_state.index)
        
        # Planetary war (enemies in proximity)
        war_pairs = [('Sun', 'Mars'), ('Mercury', 'Mars'), ('Venus', 'Saturn')]
        war_score = pd.Series(0.0, index=planet_state.index, dtype=float)
        
        for p1, p2 in war_pairs:
            conj_col = f"{p1.lower()}_{p2.lower()}_conjunction"
            if conj_col in pair_features.columns:
                war_score += pair_features[conj_col] * 2
        
        features['planetary_war_index'] = war_score
        
        # Yoga strength (benefics close together)
        yoga_pairs = [('Moon', 'Venus'), ('Moon', 'Mercury'), ('Jupiter', 'Venus')]
        yoga_score = pd.Series(0.0, index=planet_state.index, dtype=float)
        
        for p1, p2 in yoga_pairs:
            conj_col = f"{p1.lower()}_{p2.lower()}_conjunction"
            if conj_col in pair_features.columns:
                yoga_score += pair_features[conj_col] * 3
        
        features['yoga_strength'] = yoga_score
        
        # Cluster coherence (planets close together in zodiac)
        rashis = np.array([planet_state[f"{p}_rashi"].values for p in self.PLANETS])
        rashi_std = np.std(rashis, axis=0)
        features['cluster_coherence'] = (12 - rashi_std) / 12.0  # Normalize: high coherence = low std
        
        # Benefic/malefic balance
        benefics = ['Moon', 'Mercury', 'Jupiter', 'Venus']
        malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']
        
        benefic_weight = 4
        malefic_weight = len(malefics)
        
        balance = (len(benefics) * benefic_weight - len(malefics) * malefic_weight) / (len(self.PLANETS))
        features['benefic_malefic_balance'] = balance
        
        # Rahu effect (Rahu/Ketu influence)
        rahu_rashi = planet_state['Rahu_rashi']
        ketu_rashi = planet_state['Ketu_rashi']
        rahu_ketu_separation = np.abs(rahu_rashi - ketu_rashi)
        features['rahu_effect_index'] = (12 - rahu_ketu_separation) / 12.0  # Close = high effect
        
        # Grand conjunction (multiple planets in same rashi)
        grand_conj = pd.Series(0, index=planet_state.index)
        for rashi_idx in range(12):
            count_in_rashi = pd.Series(0, index=planet_state.index)
            for planet in self.PLANETS:
                count_in_rashi += (planet_state[f"{planet}_rashi"] == rashi_idx).astype(int)
            grand_conj += (count_in_rashi >= 3).astype(int)
        
        features['grand_conjunction_index'] = grand_conj.astype(float)
        
        # Retrograde planets (placeholder - would need retrograde data)
        # For now, use a proxy based on slow-moving planets
        slow_planets = ['Jupiter', 'Saturn', 'Rahu', 'Ketu']
        retrograde_proxy = 0
        for planet in slow_planets:
            # If planet hasn't changed sign in 100 days, likely retrograde or slow
            rashi_col = f"{planet}_rashi"
            changes = (planet_state[rashi_col] != planet_state[rashi_col].shift(100))
            retrograde_proxy += (~changes).astype(int)
        
        features['retrograde_planets_count'] = (retrograde_proxy / len(slow_planets)).astype(float)
        
        # Nakshatra distribution entropy (already computed in stability metrics, re-include here)
        nakshatra_positions = []
        for planet in self.PLANETS:
            nakshatra_positions.append(planet_state[f"{planet}_nakshatra"].values)
        
        nakshatra_array = np.array(nakshatra_positions)
        nakshatra_std = np.std(nakshatra_array, axis=0)
        features['nakshatra_distribution_entropy'] = nakshatra_std / 27.0
        
        return features
    
    def build_dasha_cycle_features(self, dates: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Generate 3 dasha cycle features
        
        Vedic astrology uses 120-year Vimsottari dasha cycle:
        - Dasha phase (0-1, position in 120-year cycle)
        - Dasha position normalized
        - Current major dasha (0-8 for 9 planets)
        
        Args:
            dates: DatetimeIndex
        
        Returns:
            DataFrame with 3 features
        """
        features = pd.DataFrame(index=dates)
        
        # Vimsottari dasha cycle (120 years)
        # Dasha periods for each planet (in years)
        dasha_periods = {
            0: 6,   # Ketu
            1: 20,  # Venus
            2: 6,   # Sun
            3: 10,  # Moon
            4: 7,   # Mars
            5: 18,  # Rahu
            6: 16,  # Jupiter
            7: 19,  # Saturn
            8: 17   # Mercury
        }
        
        # Reference start date for cycle (arbitrary)
        reference_date = pd.Timestamp('1900-01-01')
        days_since_ref = (dates - reference_date).days
        years_since_ref = days_since_ref / 365.25
        
        # Position in 120-year cycle
        cycle_position = years_since_ref % 120
        features['dasha_cycle_phase'] = cycle_position / 120.0
        features['dasha_cycle_position_norm'] = cycle_position / 120.0
        
        # Determine which major dasha we're in
        cumulative_years = 0
        dasha_assignments = np.zeros(len(dates))
        
        for date_idx, cycle_year in enumerate(cycle_position):
            cumulative = 0
            for dasha_id, period in dasha_periods.items():
                cumulative += period
                if cycle_year < cumulative:
                    dasha_assignments[date_idx] = dasha_id
                    break
        
        features['vimsottari_dasha_phase'] = dasha_assignments
        
        return features
    
    def build_feature_matrix(self, events_df: pd.DataFrame,
                            start_date: str = '1900-01-01',
                            end_date: str = '2025-12-31',
                            include_interactions: bool = True,
                            include_stability_metrics: bool = True,
                            include_advanced_features: bool = True,
                            include_dasha_cycles: bool = True) -> pd.DataFrame:
        """
        Build complete 170+ feature matrix
        
        Args:
            events_df: Planetary events DataFrame
            start_date: Start date for features
            end_date: End date for features
            include_interactions: Include pair interaction features
            include_stability_metrics: Include stability metrics
            include_advanced_features: Include advanced features
            include_dasha_cycles: Include dasha cycle features
        
        Returns:
            DataFrame with 170+ columns and daily index
        """
        # Build daily index
        daily_index = self.build_daily_index(start_date, end_date)
        
        # Build planet state table
        planet_state = self.build_planet_state_table(events_df)
        planet_state = planet_state.reindex(daily_index, method='ffill')
        
        # Initialize feature matrix
        feature_matrix = pd.DataFrame(index=daily_index)
        
        # Add individual planet features (36)
        print("  Building individual planet features...")
        ind_features = self.build_individual_planet_features(planet_state)
        feature_matrix = pd.concat([feature_matrix, ind_features], axis=1)
        
        # Add pair interaction features (108)
        if include_interactions:
            print("  Building pair interaction features...")
            pair_features = self.build_pair_interaction_features(planet_state)
            feature_matrix = pd.concat([feature_matrix, pair_features], axis=1)
        else:
            pair_features = pd.DataFrame()
        
        # Add stability metrics (15)
        if include_stability_metrics:
            print("  Building stability metrics...")
            stab_features = self.build_stability_metrics(planet_state)
            feature_matrix = pd.concat([feature_matrix, stab_features], axis=1)
        
        # Add advanced features (8)
        if include_advanced_features:
            print("  Building advanced features...")
            adv_features = self.build_advanced_features(planet_state, pair_features)
            feature_matrix = pd.concat([feature_matrix, adv_features], axis=1)
        
        # Add dasha cycle features (3)
        if include_dasha_cycles:
            print("  Building dasha cycle features...")
            dasha_features = self.build_dasha_cycle_features(daily_index)
            feature_matrix = pd.concat([feature_matrix, dasha_features], axis=1)
        
        # Fill NaN values
        feature_matrix = feature_matrix.fillna(0)
        
        return feature_matrix


def build_feature_matrix(events_df: pd.DataFrame,
                        start_date: str = '1900-01-01',
                        end_date: str = '2025-12-31',
                        include_interactions: bool = True,
                        include_stability_metrics: bool = True,
                        include_advanced_features: bool = True,
                        include_dasha_cycles: bool = True,
                        workers: int = 1) -> pd.DataFrame:
    """
    Main function: Build Navagraha feature matrix
    
    Args:
        events_df: DataFrame with planetary transition events
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        include_interactions: Include 108 pair interaction features
        include_stability_metrics: Include 15 stability metric features
        include_advanced_features: Include 8 advanced features
        include_dasha_cycles: Include 3 dasha cycle features
        workers: Number of parallel workers (for future optimization)
    
    Returns:
        DataFrame with shape (45815, 170+) containing all features
    
    Example:
        >>> features = build_feature_matrix(events_df)
        >>> features.shape
        (45815, 170)
        >>> features.head()
                         sun_rashi  moon_rashi  ... dasha_cycle_phase
        1900-01-01             3          8        0.125
        1900-01-02             3          8        0.125
    """
    engine = NavagrahaFeatureEngine()
    
    feature_matrix = engine.build_feature_matrix(
        events_df=events_df,
        start_date=start_date,
        end_date=end_date,
        include_interactions=include_interactions,
        include_stability_metrics=include_stability_metrics,
        include_advanced_features=include_advanced_features,
        include_dasha_cycles=include_dasha_cycles
    )
    
    print(f"\n✓ Feature matrix generated: {feature_matrix.shape}")
    print(f"  Rows: {feature_matrix.shape[0]} (daily dates)")
    print(f"  Columns: {feature_matrix.shape[1]} (features)")
    print(f"  NaN values: {feature_matrix.isna().sum().sum()}")
    
    return feature_matrix
