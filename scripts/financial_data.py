# data_pipeline/financial_data.py - FINAL FIX for MultiIndex columns

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# CORRECT TICKER SYMBOLS FOR YFINANCE
TICKERS = {
    'DXY': 'DX=F',           # US Dollar Index Futures
    'DJIA': '^GSPC',         # S&P 500 as proxy
    'GOLD': 'GC=F',          # Gold Futures
}

def download_financial_data(symbol: str, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Download OHLCV data from Yahoo Finance
    
    Args:
        symbol: Display name (e.g., 'DXY')
        ticker: YFinance ticker symbol (e.g., 'DX=F')
        start_date: YYYY-MM-DD format
        end_date: YYYY-MM-DD format
    
    Returns:
        DataFrame with OHLCV data
    """
    logger.info(f"Downloading {symbol} (ticker: {ticker}) from {start_date} to {end_date}...")
    
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if df.empty:
            logger.warning(f"No data returned for {ticker}")
            return pd.DataFrame()
        
        logger.info(f"Initial shape: {df.shape}")
        logger.info(f"Column type: {type(df.columns)}")
        
        # CRITICAL: Handle MultiIndex BEFORE using .str accessor
        # yfinance returns MultiIndex: [('Close', 'DX=F'), ('High', 'DX=F'), ...]
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten: keep only level 0 (Price, High, Low, Open, Close, Volume)
            df.columns = df.columns.get_level_values(0)
            logger.info(f"After flattening MultiIndex: {df.columns.tolist()}")
        
        # Reset index to make date a proper column
        df.reset_index(inplace=True)
        logger.info(f"After reset_index: {df.columns.tolist()}")
        
        # NOW we can safely use .str accessor
        # Convert all column names to lowercase
        df.columns = df.columns.str.lower().str.strip()
        logger.info(f"After lowercase: {df.columns.tolist()}")
        
        # Remove 'adj close' - we don't need it
        cols_to_drop = [col for col in df.columns if 'adj' in col]
        if cols_to_drop:
            df = df.drop(cols_to_drop, axis=1)
            logger.info(f"After dropping adj close: {df.columns.tolist()}")
        
        logger.info(f"Sample data:\n{df.head(2)}")
        
        # Validate we have required columns
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            logger.error(f"Missing columns for {symbol}: {missing}")
            logger.error(f"Available columns: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # Select and reorder columns
        df = df[required_cols].copy()
        
        # Remove NaN rows
        df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
        
        # Add symbol column
        df['symbol'] = symbol
        
        # Ensure numeric columns are correct type
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').astype('int64')
        df['date'] = pd.to_datetime(df['date'])
        
        # Final cleanup: remove any remaining NaNs
        df = df.dropna()
        
        logger.info(f"✓ Downloaded {len(df)} rows for {symbol}")
        return df
        
    except Exception as e:
        logger.error(f"✗ Failed to download {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def validate_financial_data(df: pd.DataFrame, symbol: str) -> dict:
    """Validate financial data quality"""
    if df.empty:
        return {'symbol': symbol, 'status': 'EMPTY', 'rows': 0}
    
    stats = {
        'symbol': symbol,
        'status': 'OK',
        'total_rows': len(df),
        'missing_values': df.isnull().sum().sum(),
        'missing_pct': (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100) if len(df) > 0 else 0,
        'date_range': f"{df['date'].min().date()} to {df['date'].max().date()}",
        'price_range': f"${df['close'].min():.2f} - ${df['close'].max():.2f}",
        'volume_avg': f"{df['volume'].mean():,.0f}",
    }
    
    # Check for data gaps
    df_sorted = df.sort_values('date')
    df_sorted['date_diff'] = df_sorted['date'].diff().dt.days
    gaps = (df_sorted['date_diff'] > 5).sum()
    stats['date_gaps'] = gaps
    
    return stats

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    
    for symbol, ticker in TICKERS.items():
        if symbol == 'DXY':
            start = '2015-01-01'  # Shorter test range
        elif symbol == 'DJIA':
            start = '2015-01-01'
        else:  # GOLD
            start = '2015-01-01'
        
        logger.info(f"\n{'='*70}")
        df = download_financial_data(symbol, ticker, start, END_DATE)
        stats = validate_financial_data(df, symbol)
        
        logger.info(f"\nStats for {symbol}:")
        for key, val in stats.items():
            logger.info(f"  {key}: {val}")
