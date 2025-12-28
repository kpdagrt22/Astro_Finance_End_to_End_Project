# utils/data_loader.py - Data Loading
import pandas as pd
from pathlib import Path

class DataLoader:
    """Centralized data loading"""
    
    def __init__(self):
        self.data_dir = Path('data/processed')
    
    def load_predictions(self, days=90):
        """Load predictions"""
        df = pd.read_csv(self.data_dir / 'predictions_future_90d.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df.head(days)
    
    def load_events(self):
        """Load planetary events"""
        df = pd.read_csv(self.data_dir / 'planetary_events_calendar.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def load_outlook(self, year=2025):
        """Load yearly outlook"""
        import json
        with open(self.data_dir / f'market_outlook_{year}.json') as f:
            return json.load(f)
