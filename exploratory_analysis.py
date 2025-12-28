# exploratory_analysis.py - Initial data exploration and correlation analysis (COMPLETE)

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, pearsonr
import logging

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# Database connection
DATABASE_URL = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'astro_finance')}"
engine = create_engine(DATABASE_URL)

def load_data_from_db():
    """Load all data from database"""
    logger.info("Loading data from database...")
    
    try:
        # Load financial data
        financial_df = pd.read_sql("""
            SELECT * FROM financial_data ORDER BY date
        """, engine)
        financial_df['date'] = pd.to_datetime(financial_df['date'])
        
        # Load planetary data
        planetary_df = pd.read_sql("""
            SELECT * FROM planetary_positions ORDER BY date
        """, engine)
        planetary_df['date'] = pd.to_datetime(planetary_df['date'])
        
        logger.info(f"✓ Loaded {len(financial_df)} financial records")
        logger.info(f"✓ Loaded {len(planetary_df)} planetary records")
        
        return financial_df, planetary_df
    except Exception as e:
        logger.warning(f"Database load failed: {e}. Using fallback data.")
        return pd.DataFrame(), pd.DataFrame()

def create_returns_target(financial_df, horizon=1):
    """Create forward returns as target variable"""
    financial_df = financial_df.sort_values('date').reset_index(drop=True)
    
    # Group by symbol
    returns_data = []
    for symbol in financial_df['symbol'].unique():
        symbol_df = financial_df[financial_df['symbol'] == symbol].copy()
        symbol_df['returns'] = symbol_df['close'].pct_change() * 100
        symbol_df['forward_returns'] = symbol_df['returns'].shift(-horizon)
        symbol_df['direction'] = (symbol_df['forward_returns'] > 0).astype(int)
        returns_data.append(symbol_df)
    
    return pd.concat(returns_data, ignore_index=True)

def analyze_financial_data(financial_df):
    """Analyze financial data characteristics"""
    logger.info("\n" + "=" * 70)
    logger.info("FINANCIAL DATA ANALYSIS")
    logger.info("=" * 70)
    
    for symbol in financial_df['symbol'].unique():
        symbol_data = financial_df[financial_df['symbol'] == symbol]
        logger.info(f"\n{symbol}:")
        logger.info(f"  Date range: {symbol_data['date'].min().date()} to {symbol_data['date'].max().date()}")
        logger.info(f"  Records: {len(symbol_data):,}")
        logger.info(f"  Price range: ${symbol_data['close'].min():.2f} - ${symbol_data['close'].max():.2f}")
        logger.info(f"  Avg volume: {symbol_data['volume'].mean():,.0f}")
        logger.info(f"  Missing values: {symbol_data.isnull().sum().sum():,}")

def analyze_planetary_data(planetary_df):
    """Analyze planetary data characteristics"""
    logger.info("\n" + "=" * 70)
    logger.info("PLANETARY DATA ANALYSIS")
    logger.info("=" * 70)
    
    if planetary_df.empty:
        logger.warning("No planetary data available")
        return
    
    logger.info(f"Date range: {planetary_df['date'].min().date()} to {planetary_df['date'].max().date()}")
    logger.info(f"Total records: {len(planetary_df):,}")
    logger.info(f"Missing values: {planetary_df.isnull().sum().sum():,}")
    
    # Check longitude ranges
    longitude_cols = [col for col in planetary_df.columns if 'longitude' in col]
    logger.info(f"\nLongitude ranges (0-360°):")
    for col in longitude_cols:
        planet = col.replace('_longitude', '').capitalize()
        min_val = planetary_df[col].min()
        max_val = planetary_df[col].max()
        mean_val = planetary_df[col].mean()
        logger.info(f"  {planet}: {min_val:.1f}° - {max_val:.1f}° (mean: {mean_val:.1f}°)")
    
    # Moon phase distribution
    if 'moon_phase' in planetary_df.columns:
        logger.info(f"\nMoon phase distribution:")
        logger.info(f"  Min: {planetary_df['moon_phase'].min():.1f}°")
        logger.info(f"  Max: {planetary_df['moon_phase'].max():.1f}°")
        logger.info(f"  Mean: {planetary_df['moon_phase'].mean():.1f}°")

def calculate_correlations(financial_df, planetary_df):
    """Calculate correlations between planetary positions and prices"""
    logger.info("\n" + "=" * 70)
    logger.info("PLANETARY-FINANCIAL CORRELATION ANALYSIS")
    logger.info("=" * 70)
    
    if planetary_df.empty:
        logger.warning("No planetary data for correlation analysis")
        return
    
    # Align data by date
    merged = financial_df.merge(planetary_df, on='date', how='inner')
    
    if merged.empty:
        logger.warning("No overlapping dates between financial and planetary data")
        return
    
    # Calculate returns
    for symbol in merged['symbol'].unique():
        symbol_data = merged[merged['symbol'] == symbol].copy()
        symbol_data['returns'] = symbol_data['close'].pct_change()
        
        # Drop NaN rows
        symbol_data = symbol_data.dropna(subset=['returns'])
        
        if len(symbol_data) < 30:
            logger.warning(f"  Insufficient data for {symbol} correlation analysis")
            continue
        
        logger.info(f"\n{symbol} ({len(symbol_data)} overlapping days):")
        
        # Calculate Spearman correlations with planetary features
        longitude_cols = [col for col in symbol_data.columns if 'longitude' in col]
        correlations = {}
        
        for col in longitude_cols:
            corr, pval = spearmanr(symbol_data[col], symbol_data['returns'])
            correlations[col] = {'corr': corr, 'pval': pval}
        
        # Sort by absolute correlation
        sorted_corr = sorted(correlations.items(), 
                           key=lambda x: abs(x[1]['corr']), 
                           reverse=True)
        
        logger.info(f"  Top 5 correlated planetary positions:")
        for col, stats in sorted_corr[:5]:
            planet = col.replace('_longitude', '').capitalize()
            logger.info(f"    {planet}: r={stats['corr']:.4f} (p={stats['pval']:.4f})")
        
        # Moon phase correlation
        if 'moon_phase' in symbol_data.columns:
            moon_corr, moon_pval = spearmanr(symbol_data['moon_phase'], symbol_data['returns'])
            logger.info(f"  Moon phase: r={moon_corr:.4f} (p={moon_pval:.4f})")

def data_quality_report(financial_df, planetary_df):
    """Generate data quality report"""
    logger.info("\n" + "=" * 70)
    logger.info("DATA QUALITY REPORT")
    logger.info("=" * 70)
    
    logger.info(f"\nFinancial Data:")
    logger.info(f"  Total rows: {len(financial_df):,}")
    logger.info(f"  Date range: {financial_df['date'].min().date()} to {financial_df['date'].max().date()}")
    logger.info(f"  Symbols: {sorted(financial_df['symbol'].unique())}")
    logger.info(f"  Missing values: {financial_df.isnull().sum().sum():,}")
    logger.info(f"  Data completeness: {(1 - financial_df.isnull().sum().sum() / (len(financial_df) * len(financial_df.columns))) * 100:.2f}%")
    
    if not planetary_df.empty:
        logger.info(f"\nPlanetary Data:")
        logger.info(f"  Total rows: {len(planetary_df):,}")
        logger.info(f"  Date range: {planetary_df['date'].min().date()} to {planetary_df['date'].max().date()}")
        logger.info(f"  Missing values: {planetary_df.isnull().sum().sum():,}")
        logger.info(f"  Data completeness: {(1 - planetary_df.isnull().sum().sum() / (len(planetary_df) * len(planetary_df.columns))) * 100:.2f}%")
        
        # Overlap analysis
        financial_dates = set(financial_df['date'].dt.date)
        planetary_dates = set(planetary_df['date'].dt.date)
        overlap = len(financial_dates & planetary_dates)
        
        logger.info(f"\nData Overlap:")
        logger.info(f"  Financial dates: {len(financial_dates):,}")
        logger.info(f"  Planetary dates: {len(planetary_dates):,}")
        logger.info(f"  Overlapping dates: {overlap:,}")
        logger.info(f"  Overlap percentage: {(overlap / len(financial_dates)) * 100:.2f}%")

def create_visualizations(financial_df, planetary_df):
    """Create exploratory visualizations"""
    logger.info("\nCreating visualizations...")
    
    plt.style.use('default')
    fig, axes = plt.subplots(3, 1, figsize=(15, 12))
    
    # Plot 1: Price history by symbol
    symbols = financial_df['symbol'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(symbols)))
    
    for i, symbol in enumerate(symbols):
        symbol_data = financial_df[financial_df['symbol'] == symbol].sort_values('date')
        axes[0].plot(symbol_data['date'], symbol_data['close'], 
                    label=symbol, color=colors[i], linewidth=1.5)
    
    axes[0].set_title('Financial Price History (Normalized)', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Normalized Price')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Normalize prices for better visualization
    for symbol in symbols:
        symbol_data = financial_df[financial_df['symbol'] == symbol]
        first_price = symbol_data['close'].iloc[0]
        financial_df.loc[financial_df['symbol'] == symbol, 'close_norm'] = symbol_data['close'] / first_price
    
    # Plot 2: Planetary positions (Sun + Moon longitude)
    if not planetary_df.empty:
        planetary_sorted = planetary_df.sort_values('date')
        axes[1].plot(planetary_sorted['date'], planetary_sorted['sun_longitude'], 
                    label='Sun', linewidth=1.5, alpha=0.8)
        axes[1].plot(planetary_sorted['date'], planetary_sorted['moon_longitude'], 
                    label='Moon', linewidth=1.5, alpha=0.8)
        axes[1].set_title('Planetary Positions (Ecliptic Longitude)', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Longitude (degrees)')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        axes[1].set_ylim([0, 360])
    
    # Plot 3: Moon phase
    if not planetary_df.empty and 'moon_phase' in planetary_df.columns:
        planetary_sorted = planetary_df.sort_values('date')
        axes[2].plot(planetary_sorted['date'], planetary_sorted['moon_phase'], 
                    color='steelblue', linewidth=1.5, alpha=0.8)
        axes[2].fill_between(planetary_sorted['date'], 0, planetary_sorted['moon_phase'], 
                           alpha=0.3, color='steelblue')
        axes[2].set_title('Moon Phase Cycle', fontsize=14, fontweight='bold')
        axes[2].set_ylabel('Phase (degrees)')
        axes[2].set_xlabel('Date')
        axes[2].grid(True, alpha=0.3)
        axes[2].set_ylim([0, 360])
    
    plt.tight_layout()
    plt.savefig('exploratory_analysis.png', dpi=300, bbox_inches='tight')
    logger.info("✓ Saved exploratory_analysis.png")
    plt.close()
    plt.clf()

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("PHASE 1: EXPLORATORY DATA ANALYSIS")
    logger.info("=" * 70)
    
    # Load data
    financial_df, planetary_df = load_data_from_db()
    
    if financial_df.empty:
        logger.error("No financial data found. Run 'python scripts/download_data.py' first.")
        exit(1)
    
    # Analyze
    analyze_financial_data(financial_df)
    analyze_planetary_data(planetary_df)
    calculate_correlations(financial_df, planetary_df)
    data_quality_report(financial_df, planetary_df)
    
    # Visualize
    try:
        create_visualizations(financial_df, planetary_df)
    except Exception as e:
        logger.warning(f"Could not create visualizations: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ EXPLORATORY ANALYSIS COMPLETE")
    logger.info("=" * 70)
    logger.info("\n📊 Check 'exploratory_analysis.png' for charts!")
    logger.info("🚀 Ready for Phase 2: Feature Engineering")
