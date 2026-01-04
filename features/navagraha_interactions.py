"""
Advanced multi-planet interactions and Navagraha dynamics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

PLANETS = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']

PLANETS_ENEMY_PAIRS = [
    ('sun', 'venus'),
    ('sun', 'saturn'),
    ('moon', 'mars'),
    ('mars', 'mercury'),
    ('jupiter', 'mercury'),
]

PLANETS_FRIENDLY_PAIRS = [
    ('sun', 'mars'),
    ('sun', 'jupiter'),
    ('moon', 'sun'),
    ('mars', 'sun'),
    ('mercury', 'venus'),
    ('jupiter', 'mars'),
    ('venus', 'mercury'),
]

class NavagrahaInteractionEngine:
    """Compute multi-planet interactions and Navagraha configurations."""

    def __init__(self, planet_features_df: pd.DataFrame):
        """
        Args:
            planet_features_df: Output of NavagrahaFeatureEngine.compute_individual_planet_features()
        """
        self.features = planet_features_df

    def compute_planetary_war_index(self) -> pd.Series:
        """
        Compute "Planetary War" index.

        A planetary war occurs when two planets are very close (< 1°, or same nakshatra pada).
        This is associated with increased volatility.
        """
        war_counts = []

        for idx, row in self.features.iterrows():
            war_score = 0

            for p1, p2 in PLANETS_ENEMY_PAIRS:
                naks1 = row.get(f'{p1}_current_nakshatra')
                naks2 = row.get(f'{p2}_current_nakshatra')

                if naks1 and naks2 and naks1 == naks2:
                    war_score += 2  # War between enemies: high volatility

                # Also check pada conjunction
                pada1 = row.get(f'{p1}_current_pada')
                pada2 = row.get(f'{p2}_current_pada')
                
                if pada1 and pada2 and pada1 == pada2 and naks1 == naks2:
                    war_score += 1  # Further intensified

            war_counts.append(war_score)

        return pd.Series(war_counts, index=self.features.index, name='planetary_war_index')

    def compute_planetary_yoga_strength(self) -> pd.Series:
        """
        Compute "Yoga" (auspicious combination) strength.

        Yogas form when:
        - Friendly planets conjoin or aspect
        - Benefic planets (Jupiter, Venus, Mercury, Moon) occupy good positions
        - Malefics (Mars, Saturn, Sun) are favorably aspected
        """
        yoga_scores = []

        for idx, row in self.features.iterrows():
            yoga_score = 0

            # Benefic conjunctions
            for p1, p2 in PLANETS_FRIENDLY_PAIRS:
                naks1 = row.get(f'{p1}_current_nakshatra')
                naks2 = row.get(f'{p2}_current_nakshatra')

                if naks1 and naks2 and naks1 == naks2:
                    yoga_score += 1

            # Benefic rashi placements
            benefics = ['jupiter', 'venus', 'mercury', 'moon']
            for benefic in benefics:
                rashi = row.get(f'{benefic}_current_rashi')
                # Benefics strong in specific rashis (Jupiter in Sagittarius, Venus in Libra, etc.)
                good_rashis = {
                    'jupiter': ['Sagittarius', 'Pisces'],
                    'venus': ['Libra', 'Taurus'],
                    'mercury': ['Virgo', 'Gemini'],
                    'moon': ['Cancer'],
                }
                if rashi and rashi in good_rashis.get(benefic, []):
                    yoga_score += 1

            yoga_scores.append(yoga_score)

        return pd.Series(yoga_scores, index=self.features.index, name='yoga_strength')

    def compute_planet_cluster_coherence(self) -> pd.DataFrame:
        """
        Measure how tightly planets cluster by rashi/nakshatra.

        Metrics:
        - mean_planet_separation: average distance between all pairs
        - rashi_clustering: entropy (1=uniform spread, 0=all same rashi)
        - nakshatra_clustering: entropy
        """
        from scipy.stats import entropy as scipy_entropy

        coherence_metrics = []

        for idx, row in self.features.iterrows():
            # Rashi occupancy
            rashi_counts = {}
            naks_counts = {}

            for planet in PLANETS:
                rashi = row.get(f'{planet}_current_rashi')
                naks = row.get(f'{planet}_current_nakshatra')

                if rashi:
                    rashi_counts[rashi] = rashi_counts.get(rashi, 0) + 1
                if naks:
                    naks_counts[naks] = naks_counts.get(naks, 0) + 1

            # Entropy-based clustering (lower entropy = tighter cluster)
            rashi_probs = np.array(list(rashi_counts.values())) / len(PLANETS)
            naks_probs = np.array(list(naks_counts.values())) / len(PLANETS)

            rashi_entropy = scipy_entropy(rashi_probs) if len(rashi_probs) > 0 else 0
            naks_entropy = scipy_entropy(naks_probs) if len(naks_probs) > 0 else 0

            coherence_metrics.append({
                'rashi_entropy': rashi_entropy,
                'nakshatra_entropy': naks_entropy,
                'mean_occupancy_per_rashi': len(PLANETS) / len(rashi_counts) if len(rashi_counts) > 0 else 0,
            })

        return pd.DataFrame(coherence_metrics, index=self.features.index)

    def compute_malefic_benefic_balance(self) -> pd.DataFrame:
        """
        Compute balance between malefic and benefic planet strengths.

        Malefics: Mars, Saturn, Sun, Rahu, Ketu
        Benefics: Jupiter, Venus, Mercury, Moon

        Metrics:
        - benefic_strength: count + position quality
        - malefic_strength: count + position quality
        - balance_ratio: benefic / (benefic + malefic)
        """
        balance_metrics = []

        malefics = ['mars', 'saturn', 'sun', 'rahu', 'ketu']
        benefics = ['jupiter', 'venus', 'mercury', 'moon']

        for idx, row in self.features.iterrows():
            benefic_score = 0
            malefic_score = 0

            # Benefic scoring
            for benefic in benefics:
                current_rashi = row.get(f'{benefic}_current_rashi')
                # Own/exalted rashis increase score
                benefic_good_rashis = {
                    'jupiter': ['Sagittarius', 'Pisces'],
                    'venus': ['Libra', 'Taurus'],
                    'mercury': ['Virgo', 'Gemini'],
                    'moon': ['Cancer'],
                }
                
                if current_rashi:
                    if current_rashi in benefic_good_rashis.get(benefic, []):
                        benefic_score += 2
                    else:
                        benefic_score += 1

            # Malefic scoring
            for malefic in malefics:
                current_rashi = row.get(f'{malefic}_current_rashi')
                # Debilitation rashis decrease score
                malefic_weak_rashis = {
                    'mars': ['Cancer'],
                    'saturn': ['Aries'],
                    'sun': ['Libra'],
                }
                
                if current_rashi:
                    if current_rashi in malefic_weak_rashis.get(malefic, []):
                        malefic_score += 0.5
                    else:
                        malefic_score += 1

            balance_ratio = benefic_score / (benefic_score + malefic_score) if (benefic_score + malefic_score) > 0 else 0.5

            balance_metrics.append({
                'benefic_strength': benefic_score,
                'malefic_strength': malefic_score,
                'balance_ratio': balance_ratio,
            })

        return pd.DataFrame(balance_metrics, index=self.features.index)
