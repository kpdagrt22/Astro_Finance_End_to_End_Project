# scripts/download_data.py - Complete data acquisition pipeline (FIXED for current structure)

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import logging
import sqlalchemy

# Add parent directory and scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import modules from current structure
from scripts.financial_data import download_financial_data, validate_financial_data, TICKERS
from scripts.planetary_data import compute_planetary_positions, validate_planetary_data

# Try to import database (optional - will skip if not available)
try:
    from database.connection import engine
    DATABASE_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Database not available - data will be downloaded but not saved")
    DATABASE_AVAILABLE = False
    engine = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_all_financial_data():
    """Download all financial instruments"""
    logger.info("\n" + "=" * 70)
    logger.info("DOWNLOADING FINANCIAL DATA")
    logger.info("=" * 70)
    
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    financial_stats = {}
    
    for symbol, ticker in TICKERS.items():
        # Set appropriate start dates for each instrument (full historical)
        start_dates = {
            'DXY': '1973-01-01',
            'DJIA': '1950-01-01',
            'GOLD': '1970-01-01',
        }
        
        start_date = start_dates.get(symbol, '1950-01-01')
        
        # Download
        df = download_financial_data(symbol, ticker, start_date, END_DATE)
        
        if not df.empty and DATABASE_AVAILABLE:
            # Insert into database
            try:
                df.to_sql('financial_data', engine, if_exists='append', index=False)
                logger.info(f"✓ Inserted {len(df)} rows for {symbol} into database")
            except Exception as e:
                logger.error(f"✗ Failed to insert {symbol}: {e}")
        
        # Validate
        stats = validate_financial_data(df, symbol)
        financial_stats[symbol] = stats
        
        logger.info(f"{symbol} Stats:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
    
    return financial_stats

def download_all_planetary_data(years_back: int = 10):
    """Compute planetary data for recent period (extend after verification)"""
    logger.info("\n" + "=" * 70)
    logger.info("COMPUTING PLANETARY DATA")
    logger.info("=" * 70)
    
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    START_DATE = (datetime.now() - timedelta(days=365*years_back)).strftime("%Y-%m-%d")
    
    logger.info(f"Computing {years_back} years of planetary data ({START_DATE} to {END_DATE})")
    logger.info("(Full 100 years will take 2-3 hours - extend after verification)")
    
    # Compute
    df = compute_planetary_positions(START_DATE, END_DATE)
    
    planetary_stats = {'rows': 0, 'status': 'FAILED'}
    
    if not df.empty and DATABASE_AVAILABLE:
        # Insert into database
        try:
            df.to_sql('planetary_positions', engine, if_exists='append', index=False)
            logger.info(f"✓ Inserted {len(df)} rows of planetary data into database")
            planetary_stats = validate_planetary_data(df)
        except Exception as e:
            logger.error(f"✗ Failed to insert planetary data: {e}")
    else:
        logger.warning("✗ No planetary data computed or database unavailable")
        planetary_stats = validate_planetary_data(df)
    
    logger.info("Planetary Data Stats:")
    for key, value in planetary_stats.items():
        logger.info(f"  {key}: {value}")
    
    return planetary_stats

def print_summary(financial_stats, planetary_stats):
    """Print data acquisition summary"""
    logger.info("\n" + "=" * 70)
    logger.info("DATA ACQUISITION SUMMARY")
    logger.info("=" * 70)
    
    logger.info("\nFINANCIAL INSTRUMENTS:")
    total_financial_rows = 0
    for symbol, stats in financial_stats.items():
        logger.info(f"\n{symbol}: {stats.get('status', 'UNKNOWN')}")
        if stats.get('status') == 'OK':
            logger.info(f"  Rows: {stats['total_rows']}")
            logger.info(f"  Date range: {stats['date_range']}")
            logger.info(f"  Price range: {stats['price_range']}")
            logger.info(f"  Missing: {stats['missing_pct']:.2f}%")
            total_financial_rows += stats['total_rows']
    
    logger.info(f"\nPLANETARY DATA: {planetary_stats.get('status', 'UNKNOWN')}")
    if planetary_stats.get('status') == 'OK':
        logger.info(f"  Rows: {planetary_stats['total_rows']}")
        logger.info(f"  Date range: {planetary_stats['date_range']}")
        logger.info(f"  Features: {planetary_stats['features']}")
    
    logger.info(f"\nTOTAL: {total_financial_rows:,} financial rows + {planetary_stats.get('total_rows', 0):,} planetary rows")
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ DATA ACQUISITION COMPLETE")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("1. python exploratory_analysis.py       # Analyze correlations")
    logger.info("2. Check exploratory_analysis.png      # View charts")
    logger.info("3. Ready for Phase 2: Feature Engineering!")

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("ASTRO FINANCE: DATA ACQUISITION PIPELINE")
    logger.info("=" * 70)
    
    # Download financial data (full historical range)
    financial_stats = download_all_financial_data()
    
    # Download planetary data (10 years for testing)
    planetary_stats = download_all_planetary_data(years_back=10)
    
    # Print summary
    print_summary(financial_stats, planetary_stats)
