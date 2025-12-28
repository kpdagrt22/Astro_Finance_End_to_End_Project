# scripts/compute_features.py - COMPLETE Phase 2 Feature Engineering (FIXED)

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os
import sys
from pathlib import Path
import logging
from datetime import timedelta
import warnings

warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to load env variables, set defaults if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'astro_finance')

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def load_master_data():
    """Load financial + planetary data"""
    logger.info("Loading master dataset...")
    
    financial_df = pd.read_sql("SELECT * FROM financial_data ORDER BY date", engine)
    planetary_df = pd.read_sql("SELECT * FROM planetary_positions ORDER BY date", engine)
    
    financial_df['date'] = pd.to_datetime(financial_df['date'])
    planetary_df['date'] = pd.to_datetime(planetary_df['date'])
    
    # Merge on date
    master_df = financial_df.merge(planetary_df, on='date', how='inner')
    logger.info(f"✓ Master dataset: {len(master_df):,} overlapping days")
    
    return master_df.sort_values('date').reset_index(drop=True)

def create_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """40+ price-based features"""
    logger.info("Creating price features...")
    
    # Lag returns (1-90 days) per symbol
    for days in [1, 3, 7, 14, 21, 30, 60, 90]:
        for symbol in df['symbol'].unique():
            mask = df['symbol'] == symbol
            df[f'{symbol.lower()}_return_{days}d'] = df.loc[mask, 'close'].pct_change(days)
    
    # Rolling statistics per symbol
    for window in [7, 14, 21, 30]:
        df[f'close_mean_{window}d'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(window).mean())
        df[f'close_std_{window}d'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(window).std())
        df[f'volume_mean_{window}d'] = df.groupby('symbol')['volume'].transform(lambda x: x.rolling(window).mean())
    
    # Cross-asset ratios
    symbols = sorted(df['symbol'].unique())
    for i, s1 in enumerate(symbols):
        for s2 in symbols[i+1:]:
            ratio_col = f'{s1.lower()}_{s2.lower()}_ratio'
            s1_prices = df[df['symbol']==s1]['close']
            s2_prices = df[df['symbol']==s2]['close']
            df[ratio_col] = (s1_prices / s2_prices).reindex(df.index, method='ffill')
    
    logger.info(f"✓ Created price features")
    return df

def create_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """RSI, MACD, Bollinger Bands (20 features)"""
    logger.info("Creating technical indicators...")
    
    def rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def macd(series, fast=12, slow=26, signal=9):
        ema_fast = series.ewm(span=fast).mean()
        ema_slow = series.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    for symbol in df['symbol'].unique():
        mask = df['symbol'] == symbol
        prices = df.loc[mask, 'close'].copy()
        
        # RSI (multiple periods)
        df.loc[mask, f'rsi_14_{symbol.lower()}'] = rsi(prices, 14)
        df.loc[mask, f'rsi_21_{symbol.lower()}'] = rsi(prices, 21)
        
        # MACD
        macd_line, signal_line, histogram = macd(prices)
        df.loc[mask, f'macd_{symbol.lower()}'] = macd_line
        df.loc[mask, f'macd_signal_{symbol.lower()}'] = signal_line
        df.loc[mask, f'macd_hist_{symbol.lower()}'] = histogram
        
        # Bollinger Bands (20-day)
        prices_20 = prices.rolling(20).mean()
        std_20 = prices.rolling(20).std()
        df.loc[mask, f'bb_position_{symbol.lower()}'] = (prices - (prices_20 - 2*std_20)) / (4*std_20)
    
    logger.info("✓ Created 20 technical indicators")
    return df

def create_planetary_aspects(df: pd.DataFrame) -> pd.DataFrame:
    """36+ aspect features (conjunction, opposition, trine, square)"""
    logger.info("Creating planetary aspects...")
    
    planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
    aspects = {
        'conjunction': 0,    # 0°
        'sextile': 60,       # 60°
        'square': 90,        # 90°
        'trine': 120,        # 120°
        'quincunx': 150,     # 150°
        'opposition': 180    # 180°
    }
    orb = 6.0  # 6° tolerance
    
    aspect_count = 0
    
    for i, p1 in enumerate(planets):
        for p2 in planets[i+1:]:
            lon1_col = f'{p1}_longitude'
            lon2_col = f'{p2}_longitude'
            
            if lon1_col in df.columns and lon2_col in df.columns:
                # Angular separation (shortest arc)
                diff = np.minimum(
                    np.abs(df[lon1_col] - df[lon2_col]) % 360,
                    360 - np.abs(df[lon1_col] - df[lon2_col]) % 360
                )
                
                for aspect_name, angle in aspects.items():
                    col_name = f'{p1}_{p2}_{aspect_name}'
                    df[col_name] = (np.abs(diff - angle) <= orb).astype(int)
                    aspect_count += 1
    
    logger.info(f"✓ Created {aspect_count} planetary aspect features")
    return df

def create_motion_features(df: pd.DataFrame) -> pd.DataFrame:
    """Enhanced retrograde + angular velocity (25+ features)"""
    logger.info("Creating enhanced motion features...")
    
    planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
    
    for planet in planets:
        lon_col = f'{planet}_longitude'
        if lon_col in df.columns:
            # Daily motion (handle 360° wrap-around)
            motion = np.diff(df[lon_col], prepend=df[lon_col].iloc[0])
            motion = ((motion + 180) % 360 - 180)  # Normalize to -180° to +180°
            
            # Retrograde indicator
            df[f'{planet}_retrograde'] = (motion < 0).astype(int)
            
            # Angular velocity
            df[f'{planet}_velocity'] = motion
            
            # Retrograde duration (consecutive days)
            retro_mask = df[f'{planet}_retrograde'] == 1
            df[f'{planet}_retro_duration'] = retro_mask.groupby(
                (retro_mask != retro_mask.shift()).cumsum()
            ).cumcount() + 1
            df[f'{planet}_retro_duration'] = df[f'{planet}_retro_duration'].where(retro_mask, 0)
            
            # Velocity extremes (7-day window)
            df[f'{planet}_velocity_max_7d'] = df[f'{planet}_velocity'].rolling(7).max()
            df[f'{planet}_velocity_min_7d'] = df[f'{planet}_velocity'].rolling(7).min()
    
    # Multi-planet retrograde combinations
    retrograde_cols = [f'{p}_retrograde' for p in ['mercury', 'venus', 'mars', 'jupiter', 'saturn']]
    retrograde_cols = [col for col in retrograde_cols if col in df.columns]
    
    if len(retrograde_cols) >= 2:
        df['retrograde_count'] = df[retrograde_cols].sum(axis=1)
        df['inner_planets_retro'] = df[['mercury_retrograde', 'venus_retrograde']].sum(axis=1)
        df['outer_planets_retro'] = df[['mars_retrograde', 'jupiter_retrograde', 'saturn_retrograde']].sum(axis=1)
    
    logger.info(f"✓ Created motion/retrograde features")
    return df

def create_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Forward returns + direction targets (20 features)"""
    logger.info("Creating target variables...")
    
    horizons = [1, 3, 5, 10, 21]
    
    for symbol in df['symbol'].unique():
        mask = df['symbol'] == symbol
        closes = df.loc[mask, 'close'].values
        indices = df.loc[mask].index
        
        for h in horizons:
            # Forward returns
            fwd_returns = np.full(len(closes), np.nan)
            for i in range(len(closes) - h):
                fwd_returns[i] = (closes[i+h] - closes[i]) / closes[i]
            df.loc[indices, f'{symbol.lower()}_fwd_return_{h}d'] = fwd_returns
            
            # Direction
            df.loc[indices, f'{symbol.lower()}_fwd_direction_{h}d'] = (fwd_returns > 0).astype(int)
    
    logger.info("✓ Created 20 target features")
    return df

def main():
    """Complete Phase 2 pipeline"""
    logger.info("=" * 80)
    logger.info("🚀 PHASE 2: COMPLETE FEATURE ENGINEERING")
    logger.info("=" * 80)
    
    # Load data
    df = load_master_data()
    
    original_cols = len(df.columns)
    
    # Create ALL features
    df = create_price_features(df)
    df = create_technical_indicators(df)
    df = create_planetary_aspects(df)
    df = create_motion_features(df)
    df = create_targets(df)
    
    # Clean data
    df = df.dropna(thresh=len(df.columns) * 0.7)
    
    logger.info(f"📊 Final dataset: {len(df):,} rows × {len(df.columns):,} features (+{len(df.columns) - original_cols} new)")
    
    # Save full features
    df.to_parquet('features_full.parquet', index=False)
    logger.info("✓ Saved features_full.parquet")
    
    # Get numeric columns for variance analysis
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Top features by variance
    variances = df[numeric_cols].var().sort_values(ascending=False)
    top_variance = variances.head(100).index.tolist()
    
    logger.info(f"\nTop 10 most variable features:")
    for i, (feat, var) in enumerate(variances.head(10).items(), 1):
        logger.info(f"  {i:2d}. {feat:30s} variance={var:.6f}")
    
    # Save selected features with metadata
    selected_cols = top_variance + ['date', 'symbol']
    df[selected_cols].to_parquet('features_selected.parquet', index=False)
    logger.info("✓ Saved features_selected.parquet (TOP 100 + metadata)")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ PHASE 2 COMPLETE - READY FOR ML MODELING!")
    logger.info(f"📊 Dataset: {len(df):,} rows × {len(df.columns):,} total features")
    logger.info(f"🎯 Selected: 100 top features + metadata")
    logger.info("🚀 Next: python scripts/train_models.py")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
