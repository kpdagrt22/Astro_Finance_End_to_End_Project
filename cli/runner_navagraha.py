#!/usr/bin/env python
"""
One-command orchestrator for all 9 planets (Navagraha) + features + labels + models.

Usage:
    python cli/runner_navagraha.py --config config/pipeline_navagraha.yaml
"""

import argparse
import logging
import yaml
from pathlib import Path
import pandas as pd
import sys

from drikpanchang_scraper import backfill_all
from features import NavagrahaFeatureEngine, NavagrahaInteractionEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pipeline(config_path: Path):
    """Execute full Navagraha pipeline."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    output_dir = Path(config['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 80)
    logger.info("NAVAGRAHA (9-PLANET) ASTRO-FINANCIAL FORECASTING PIPELINE")
    logger.info("=" * 80)

    # Step 1: Scrape all planets
    if config['scraping']['enabled']:
        logger.info("\n[STEP 1] Scraping DrikPanchang for all 9 planets...")
        results = backfill_all(
            start_year=config['scraping']['start_year'],
            end_year=config['scraping']['end_year'],
            location=config['scraping']['location'],
            endpoint_types=config['scraping'].get('endpoint_types', ['rashi', 'nakshatra', 'pada']),
        )
        logger.info(f"✓ Scraped {len(results)-1} (planet, endpoint) pairs")

    # Step 2: Feature engineering
    if config['feature_engineering']['enabled']:
        logger.info("\n[STEP 2] Engineering Navagraha features...")
        
        events_df = pd.read_csv("data/processed/drikpanchang/events_all_planets_merged.csv")
        
        feature_engine = NavagrahaFeatureEngine(events_df)
        
        # Generate observation dates (e.g., daily or weekly)
        date_range = pd.date_range(
            start='1900-01-01',
            end='2025-12-31',
            freq=config['feature_engineering'].get('frequency', 'D')  # Daily by default
        )
        
        logger.info(f"Computing features for {len(date_range)} observation dates...")
        
        # Individual planet features
        planet_features = feature_engine.compute_individual_planet_features(date_range)
        logger.info(f"✓ Computed {len(planet_features.columns)} individual planet features")
        
        # Navagraha stability
        stability = feature_engine.compute_navagraha_stability(date_range)
        logger.info(f"✓ Computed {len(stability.columns)} stability features")
        
        # Planet pair interactions
        interactions = feature_engine.compute_planet_pair_interactions(date_range)
        logger.info(f"✓ Computed {len(interactions.columns)} interaction features")
        
        # Merge all features
        all_features = pd.concat([planet_features, stability, interactions], axis=1)
        all_features.to_csv(output_dir / 'navagraha_features.csv')
        logger.info(f"✓ Saved all features: {len(all_features.columns)} columns")
        
    # Step 3: Advanced interactions
    if config['feature_engineering'].get('advanced_interactions', False):
        logger.info("\n[STEP 3] Computing advanced Navagraha interactions...")
        
        interaction_engine = NavagrahaInteractionEngine(planet_features)
        
        war_index = interaction_engine.compute_planetary_war_index()
        yoga_strength = interaction_engine.compute_planetary_yoga_strength()
        cluster_coherence = interaction_engine.compute_planet_cluster_coherence()
        balance = interaction_engine.compute_malefic_benefic_balance()
        
        advanced = pd.concat([war_index, yoga_strength, cluster_coherence, balance], axis=1)
        advanced.to_csv(output_dir / 'navagraha_advanced_interactions.csv')
        logger.info(f"✓ Saved advanced interactions: {len(advanced.columns)} columns")

    logger.info("\n" + "=" * 80)
    logger.info("NAVAGRAHA PIPELINE COMPLETE")
    logger.info(f"Results saved to: {output_dir}")
    logger.info("=" * 80)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Navagraha (9-Planet) Pipeline Runner')
    parser.add_argument('--config', type=Path, default=Path('config/pipeline_navagraha.yaml'))
    args = parser.parse_args()

    if not args.config.exists():
        logger.error(f"Config not found: {args.config}")
        sys.exit(1)

    run_pipeline(args.config)
