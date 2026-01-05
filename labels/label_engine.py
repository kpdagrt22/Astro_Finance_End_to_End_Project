"""
Label Engineering: Market Regime Classification

Generates crash/normal labels from financial data using multiple strategies:
- Drawdown-based (recent peak decline)
- Volatility-based (elevated daily volatility)
- Event-based (proximity to planetary events)
- Combined voting (majority rule across strategies)

Includes class weighting for imbalance handling.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')


class LabelEngine:
    """Generate market regime labels from price and event data"""
    
    def __init__(self):
        """Initialize label engine"""
        self.price_df = None
        self.events_df = None
        self.labels_dict = {}
    
    def label_drawdown(self, price_df: pd.DataFrame, 
                       threshold: float = 0.10) -> pd.Series:
        """
        Label crash based on drawdown from recent peak
        
        A drawdown crash occurs when:
        - Price falls more than threshold (e.g., 10%) from recent 252-day high
        
        Args:
            price_df: DataFrame with 'close' column
            threshold: Drawdown threshold (default 0.10 = 10%)
        
        Returns:
            Series with 0/1 labels (1 = crash, 0 = normal)
        """
        if 'close' not in price_df.columns:
            return pd.Series(0, index=price_df.index)
        
        close = price_df['close'].copy()
        
        # Calculate rolling maximum
        rolling_max = close.rolling(window=252, min_periods=1).max()
        
        # Calculate drawdown
        drawdown = (close - rolling_max) / rolling_max
        
        # Label crash if drawdown > threshold
        labels = (drawdown <= -threshold).astype(int)
        
        return labels
    
    def label_volatility(self, price_df: pd.DataFrame,
                        threshold: float = 0.02) -> pd.Series:
        """
        Label crash based on elevated volatility
        
        A volatility crash occurs when:
        - Rolling 20-day std of returns > threshold (e.g., 2%)
        
        Args:
            price_df: DataFrame with 'close' column
            threshold: Volatility threshold (default 0.02 = 2%)
        
        Returns:
            Series with 0/1 labels (1 = crash, 0 = normal)
        """
        if 'close' not in price_df.columns:
            return pd.Series(0, index=price_df.index)
        
        close = price_df['close'].copy()
        
        # Calculate returns
        returns = close.pct_change()
        
        # Calculate rolling volatility
        rolling_vol = returns.rolling(window=20, min_periods=1).std()
        
        # Label crash if volatility > threshold
        labels = (rolling_vol > threshold).astype(int)
        
        return labels
    
    def label_event_based(self, events_df: pd.DataFrame,
                         price_df: pd.DataFrame,
                         window_days: int = 30) -> pd.Series:
        """
        Label crash based on proximity to major planetary events
        
        An event-based crash occurs when:
        - Price drops significantly within window_days after a major event
        
        Args:
            events_df: DataFrame with event dates
            price_df: DataFrame with 'close' column
            window_days: Days after event to consider (default 30)
        
        Returns:
            Series with 0/1 labels (1 = crash near event, 0 = normal)
        """
        labels = pd.Series(0, index=price_df.index, dtype=int)
        
        if events_df.empty or 'close' not in price_df.columns:
            return labels
        
        close = price_df['close'].copy()
        
        try:
            # Get major event dates
            event_dates = pd.to_datetime(events_df.get('event_utc_dt', pd.Series()), errors='coerce')
            event_dates = event_dates.dropna().unique()
            
            # Mark event windows
            for event_date in event_dates:
                event_window = pd.date_range(start=event_date, periods=window_days, freq='D')
                
                # Check if price declined in window
                window_data = close[close.index.isin(event_window)]
                if len(window_data) > 0:
                    pct_change = (window_data.iloc[-1] - window_data.iloc[0]) / window_data.iloc[0]
                    if pct_change < -0.05:  # 5% decline threshold
                        labels[close.index.isin(event_window)] = 1
        except:
            pass
        
        return labels
    
    def label_combined(self, label_drawdown: pd.Series,
                      label_volatility: pd.Series,
                      label_event: pd.Series,
                      voting: str = 'majority') -> pd.Series:
        """
        Combine multiple labeling strategies using voting
        
        Args:
            label_drawdown: Drawdown labels (0/1)
            label_volatility: Volatility labels (0/1)
            label_event: Event labels (0/1)
            voting: Voting method ('majority' or 'unanimous')
        
        Returns:
            Series with 0/1 labels
        """
        # Stack labels
        stacked = pd.DataFrame({
            'drawdown': label_drawdown,
            'volatility': label_volatility,
            'event': label_event
        })
        
        # Count crash votes
        crash_votes = stacked.sum(axis=1)
        
        if voting == 'majority':
            combined = (crash_votes >= 2).astype(int)
        elif voting == 'unanimous':
            combined = (crash_votes == 3).astype(int)
        else:
            combined = (crash_votes >= 2).astype(int)
        
        return combined
    
    def compute_class_weights(self, labels: pd.Series) -> Dict[int, float]:
        """
        Compute class weights to handle imbalanced data
        
        Args:
            labels: Series with 0/1 labels
        
        Returns:
            Dict with weights for each class
        """
        value_counts = labels.value_counts()
        
        weights = {}
        for class_val in [0, 1]:
            if class_val in value_counts.index:
                count = value_counts[class_val]
                weight = len(labels) / (2 * count)
                weights[class_val] = weight
            else:
                weights[class_val] = 1.0
        
        return weights
    
    def generate_labels(self,
                       price_df: pd.DataFrame,
                       events_df: pd.DataFrame = None,
                       strategies: List[str] = None,
                       drawdown_threshold: float = 0.10,
                       volatility_threshold: float = 0.02,
                       event_window_days: int = 30) -> pd.DataFrame:
        """
        Generate all labels and return as DataFrame
        
        Args:
            price_df: DataFrame with 'close' column
            events_df: Optional DataFrame with event dates
            strategies: List of strategies to include
            drawdown_threshold: Drawdown threshold (default 0.10)
            volatility_threshold: Volatility threshold (default 0.02)
            event_window_days: Event window in days (default 30)
        
        Returns:
            DataFrame with label columns
        """
        if events_df is None:
            events_df = pd.DataFrame()
        
        if strategies is None:
            strategies = ['drawdown', 'volatility', 'event', 'combined']
        
        # Initialize result DataFrame
        labels_result = pd.DataFrame(index=price_df.index)
        
        # Generate labels
        if 'drawdown' in strategies or 'combined' in strategies:
            label_dd = self.label_drawdown(price_df, drawdown_threshold)
            labels_result['label_drawdown'] = label_dd
        else:
            label_dd = pd.Series(0, index=price_df.index)
        
        if 'volatility' in strategies or 'combined' in strategies:
            label_vol = self.label_volatility(price_df, volatility_threshold)
            labels_result['label_volatility'] = label_vol
        else:
            label_vol = pd.Series(0, index=price_df.index)
        
        if 'event' in strategies or 'combined' in strategies:
            label_evt = self.label_event_based(events_df, price_df, event_window_days)
            labels_result['label_event'] = label_evt
        else:
            label_evt = pd.Series(0, index=price_df.index)
        
        if 'combined' in strategies:
            label_comb = self.label_combined(label_dd, label_vol, label_evt)
            labels_result['label_combined'] = label_comb
        else:
            label_comb = pd.Series(0, index=price_df.index)
        
        # Compute class weights
        weights = self.compute_class_weights(label_comb)
        labels_result['class_weight'] = label_comb.map(weights)
        
        return labels_result


def generate_labels(price_df: pd.DataFrame,
                   events_df: pd.DataFrame = None,
                   strategies: List[str] = None,
                   drawdown_threshold: float = 0.10,
                   volatility_threshold: float = 0.02,
                   event_window_days: int = 30) -> pd.DataFrame:
    """
    Main function: Generate market regime labels
    
    Args:
        price_df: DataFrame with 'close' column
        events_df: DataFrame with event dates (optional)
        strategies: List of strategies
        drawdown_threshold: Threshold for drawdown (default 0.10)
        volatility_threshold: Threshold for volatility (default 0.02)
        event_window_days: Window after event (default 30)
    
    Returns:
        DataFrame with label columns
    """
    engine = LabelEngine()
    
    labels = engine.generate_labels(
        price_df=price_df,
        events_df=events_df,
        strategies=strategies if strategies else ['drawdown', 'volatility', 'event', 'combined'],
        drawdown_threshold=drawdown_threshold,
        volatility_threshold=volatility_threshold,
        event_window_days=event_window_days
    )
    
    return labels
