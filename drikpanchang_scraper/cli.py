import argparse
import logging
from pathlib import Path
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Try Skyfield first, fallback to Swiss Ephemeris
    try:
        from .ephemeris_skyfield import SkyFieldEphemerisEngine as Engine
        logger.info("Using Skyfield backend")
    except ImportError:
        try:
            from .ephemeris import VedicEphemerisEngine as Engine
            logger.info("Using Swiss Ephemeris backend")
        except ImportError:
            logger.error("Neither Skyfield nor Swiss Ephemeris available!")
            logger.info("Install: pip install skyfield")
            sys.exit(1)

    parser = argparse.ArgumentParser(
        description='Compute Navagraha (9-planet) gochar transitions.'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        default=1900,
        help='Start year (default: 1900)'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        default=2025,
        help='End year (default: 2025)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory (default: data/processed/drikpanchang/)'
    )

    args = parser.parse_args()

    logger.info(f"Computing Navagraha ephemeris: {args.start_year}-{args.end_year}")
    
    results = Engine.compute_all_planets(
        start_year=args.start_year,
        end_year=args.end_year,
        output_dir=args.output_dir,
    )
    
    logger.info(f"\n{'='*80}")
    logger.info(f"COMPUTATION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Computed {len(results)-1} (planet, endpoint) pairs")
    if args.output_dir:
        logger.info(f"Output directory: {args.output_dir}")

if __name__ == '__main__':
    main()
