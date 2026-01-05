"""
Validation: Walk-Forward Time Series Cross-Validation

Implements time-series safe validation:
- No look-ahead bias
- Rolling window approach
- Multiple folds for robust evaluation
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from sklearn.model_selection import train_test_split
from models.ml_models import compute_metrics, train_models
import warnings

warnings.filterwarnings('ignore')


class WalkForwardValidator:
    """Time-series safe cross-validation"""
    
    def __init__(self, data: pd.DataFrame,
                 train_years: int = 50,
                 test_years: int = 5,
                 stride_years: int = 5):
        """Initialize walk-forward validator"""
        self.data = data
        self.train_years = train_years
        self.test_years = test_years
        self.stride_years = stride_years
        self.folds = self._generate_folds()
    
    def _generate_folds(self) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Generate train/test index pairs"""
        folds = []
        
        dates = self.data.index
        min_year = dates[0].year
        max_year = dates[-1].year
        
        train_start_year = min_year
        
        while True:
            train_end_year = train_start_year + self.train_years
            test_start_year = train_end_year
            test_end_year = test_start_year + self.test_years
            
            if test_end_year > max_year:
                break
            
            train_mask = (dates.year >= train_start_year) & (dates.year < train_end_year)
            test_mask = (dates.year >= test_start_year) & (dates.year < test_end_year)
            
            train_idx = np.where(train_mask)[0]
            test_idx = np.where(test_mask)[0]
            
            if len(train_idx) > 0 and len(test_idx) > 0:
                folds.append((train_idx, test_idx))
            
            train_start_year += self.stride_years
        
        return folds
    
    def get_folds(self) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Get all train/test fold indices"""
        return self.folds


def walk_forward_splits(data: pd.DataFrame,
                       train_years: int = 50,
                       test_years: int = 5,
                       stride_years: int = 5) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Generate walk-forward validation splits
    
    Args:
        data: DataFrame with datetime index
        train_years: Training window in years
        test_years: Test window in years
        stride_years: Step size in years
    
    Returns:
        List of (train_indices, test_indices) tuples
    """
    validator = WalkForwardValidator(
        data=data,
        train_years=train_years,
        test_years=test_years,
        stride_years=stride_years
    )
    
    return validator.get_folds()


def run_walk_forward_validation(X: pd.DataFrame,
                               y: pd.Series,
                               class_weights: Optional[Dict[int, float]] = None,
                               train_years: int = 50,
                               test_years: int = 5,
                               stride_years: int = 5,
                               random_state: int = 42) -> pd.DataFrame:
    """
    Run complete walk-forward validation
    
    Args:
        X: Feature DataFrame
        y: Labels Series
        class_weights: Optional class weights
        train_years: Training window
        test_years: Test window
        stride_years: Stride size
        random_state: Random seed
    
    Returns:
        DataFrame with metrics per fold per model
    """
    # Combine X and y
    combined = pd.concat([X, y], axis=1)
    combined.columns = list(X.columns) + ['label']
    
    # Generate folds
    folds = walk_forward_splits(
        combined,
        train_years=train_years,
        test_years=test_years,
        stride_years=stride_years
    )
    
    print(f"\n  Generated {len(folds)} walk-forward folds")
    
    all_metrics = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(folds):
        print(f"  Processing fold {fold_idx + 1}/{len(folds)}...")
        
        # Split data
        X_train_fold = X.iloc[train_idx].copy()
        y_train_fold = y.iloc[train_idx].copy()
        X_test_fold = X.iloc[test_idx].copy()
        y_test_fold = y.iloc[test_idx].copy()
        
        # Further split train into train/val
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_fold, y_train_fold,
            test_size=0.2,
            random_state=random_state,
            stratify=y_train_fold if len(y_train_fold.unique()) > 1 else None
        )
        
        # Prepare sample weights
        sample_weight = None
        if class_weights:
            sample_weight = np.array([class_weights.get(int(label), 1.0) for label in y_train])
        
        # Train models
        trained_models = train_models(
            X_train, y_train,
            X_val, y_val,
            sample_weight=sample_weight,
            random_state=random_state
        )
        
        # Evaluate each model
        for model_name, model in trained_models.items():
            y_pred_proba = model.predict_proba(X_test_fold)
            y_pred = (y_pred_proba > 0.5).astype(int)
            
            metrics = compute_metrics(y_test_fold.values, y_pred_proba, y_pred)
            metrics['model'] = model_name
            metrics['fold'] = fold_idx
            
            all_metrics.append(metrics)
    
    metrics_df = pd.DataFrame(all_metrics)
    
    print(f"\n✓ Walk-forward validation complete")
    print(f"  Total folds: {len(folds)}")
    print(f"  Models evaluated: {metrics_df['model'].nunique()}")
    
    return metrics_df


def summarize_metrics(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize metrics by model
    
    Args:
        metrics_df: Output from run_walk_forward_validation
    
    Returns:
        Summary DataFrame
    """
    summary_stats = {}
    
    for model_name in metrics_df['model'].unique():
        model_data = metrics_df[metrics_df['model'] == model_name]
        
        summary_stats[model_name] = {
            'auc_mean': model_data['auc'].mean(),
            'auc_std': model_data['auc'].std(),
            'f1_mean': model_data['f1'].mean(),
            'f1_std': model_data['f1'].std(),
            'n_folds': len(model_data)
        }
    
    summary_df = pd.DataFrame(summary_stats).T
    summary_df = summary_df.sort_values('auc_mean', ascending=False)
    
    return summary_df
