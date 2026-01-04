import logging
from pathlib import Path
from typing import List, Optional, Dict
import pandas as pd
from tqdm import tqdm

from .fetch import fetch_year_html, fetch_all_planets_year, PLANETS
from .parse import parse_planet

logger = logging.getLogger(__name__)

def backfill_all(
    start_year: int = 1900,
    end_year: int = 2025,
    location: str = 'New Delhi, India',
    output_dir: Optional[Path] = None,
    endpoint_types: List[str] = None,
) -> dict:
    """
    Backfill all planets (9 Navagraha) for all endpoint types.

    Args:
        start_year: Start year (e.g., 1900)
        end_year: End year (e.g., 2025)
        location: Location string
        output_dir: Output directory. Defaults to data/processed/drikpanchang/
        endpoint_types: List of endpoint types ['rashi', 'nakshatra', 'pada']. Default: all 3

    Returns:
        Dict mapping (planet, endpoint_type) -> DataFrame
    """
    if endpoint_types is None:
        endpoint_types = ['rashi', 'nakshatra', 'pada']
    
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'data' / 'processed' / 'drikpanchang'
    output_dir.mkdir(parents=True, exist_ok=True)

    all_dfs = {}
    merged_rows = []

    logger.info(f"\n{'='*80}")
    logger.info(f"BACKFILLING ALL PLANETS: {start_year}-{end_year}")
    logger.info(f"Endpoint types: {endpoint_types}")
    logger.info(f"{'='*80}\n")

    for planet in PLANETS:
        for endpoint_type in endpoint_types:
            logger.info(f"\nProcessing {planet.upper()} - {endpoint_type.upper()}")
            logger.info(f"-" * 60)

            endpoint_dfs = []

            for year in tqdm(range(start_year, end_year + 1), desc=f"{planet}_{endpoint_type}"):
                html = fetch_year_html(year, planet, endpoint_type, location, use_cache=True)

                if html:
                    try:
                        df = parse_planet(html, planet, endpoint_type, year)
                        if not df.empty:
                            endpoint_dfs.append(df)
                            merged_rows.extend(df.to_dict('records'))
                    except Exception as e:
                        logger.error(f"Error parsing {planet} {endpoint_type} for year {year}: {e}")
                else:
                    logger.debug(f"Failed to fetch {planet} {endpoint_type} for year {year}")

            # Save endpoint-specific file
            if endpoint_dfs:
                combined_df = pd.concat(endpoint_dfs, ignore_index=True)
                all_dfs[(planet, endpoint_type)] = combined_df

                endpoint_file = output_dir / f"events_{planet}_{endpoint_type}.csv"
                combined_df.to_csv(endpoint_file, index=False)
                logger.info(f"✓ Saved: {endpoint_file} ({len(combined_df)} events)")
            else:
                logger.warning(f"No data for {planet} {endpoint_type}")

    # Save merged file for all planets
    if merged_rows:
        merged_df = pd.DataFrame(merged_rows)
        merged_file = output_dir / 'events_all_planets_merged.csv'
        merged_df.to_csv(merged_file, index=False)
        logger.info(f"\n✓ Merged all planets: {merged_file} ({len(merged_df)} total events)")
        all_dfs['merged'] = merged_df

    # Summary statistics
    logger.info(f"\n{'='*80}")
    logger.info("BACKFILL COMPLETE - SUMMARY")
    logger.info(f"{'='*80}")
    for planet in PLANETS:
        for endpoint_type in endpoint_types:
            key = (planet, endpoint_type)
            if key in all_dfs:
                logger.info(f"{planet:8s} {endpoint_type:10s}: {len(all_dfs[key]):6d} events")

    return all_dfs
