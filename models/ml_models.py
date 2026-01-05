"""
ML Models: Regime Classification

Three classifier architectures for market regime prediction:
1. XGBoostRegimeClassifier - Gradient boosting
2. LightGBMRegimeClassifier - Light gradient boosting
3. EnsembleRegimeClassifier - Probability voting ensemble
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any
import xgboost as xgb
import lightgbm as lgb
from sklearn.metrics import (
    roc_auc_score, accuracy_score, f1_score, precision_score,
    recall_score, brier_score_loss, log_loss
)
import warnings

warnings.filterwarnings('ignore')


class XGBoostRegimeClassifier:
    """XGBoost gradient boosting classifier"""
    
    def __init__(self, random_state: int = 42):
        """Initialize XGBoost classifier"""
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            eval_metric='auc',
            verbosity=0,
            tree_method='hist'
        )
        self.is_trained = False
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series,
            X_val: Optional[pd.DataFrame] = None,
            y_val: Optional[pd.Series] = None,
            sample_weight: Optional[np.ndarray] = None) -> None:
        """Train XGBoost model"""
        eval_set = []
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]
        
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            sample_weight=sample_weight,
            verbose=False
        )
        self.is_trained = True
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get probability predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        return self.model.predict_proba(X)[:, 1]
    
    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Get class predictions"""
        proba = self.predict_proba(X)
        return (proba > threshold).astype(int)


class LightGBMRegimeClassifier:
    """LightGBM gradient boosting classifier"""
    
    def __init__(self, random_state: int = 42):
        """Initialize LightGBM classifier"""
        self.model = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            verbose=-1,
            num_leaves=31
        )
        self.is_trained = False
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series,
            X_val: Optional[pd.DataFrame] = None,
            y_val: Optional[pd.Series] = None,
            sample_weight: Optional[np.ndarray] = None) -> None:
        """Train LightGBM model"""
        callbacks = [lgb.early_stopping(stopping_rounds=10, verbose=False)]
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)] if X_val is not None else None,
            sample_weight=sample_weight,
            callbacks=callbacks
        )
        self.is_trained = True
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get probability predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        return self.model.predict_proba(X)[:, 1]
    
    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Get class predictions"""
        proba = self.predict_proba(X)
        return (proba > threshold).astype(int)


class EnsembleRegimeClassifier:
    """Ensemble classifier combining XGBoost and LightGBM"""
    
    def __init__(self, xgb_model: XGBoostRegimeClassifier,
                 lgb_model: LightGBMRegimeClassifier,
                 weights: Optional[Dict[str, float]] = None):
        """Initialize ensemble"""
        self.xgb_model = xgb_model
        self.lgb_model = lgb_model
        
        if weights is None:
            self.weights = {'xgb': 0.5, 'lgb': 0.5}
        else:
            self.weights = weights
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get ensemble probability predictions"""
        xgb_proba = self.xgb_model.predict_proba(X)
        lgb_proba = self.lgb_model.predict_proba(X)
        
        ensemble_proba = (
            self.weights['xgb'] * xgb_proba +
            self.weights['lgb'] * lgb_proba
        )
        
        return ensemble_proba
    
    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Get ensemble class predictions"""
        proba = self.predict_proba(X)
        return (proba > threshold).astype(int)


def compute_metrics(y_true: np.ndarray, y_pred_proba: np.ndarray,
                   y_pred: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Compute comprehensive evaluation metrics
    
    Args:
        y_true: True labels (0/1)
        y_pred_proba: Predicted probabilities (0-1)
        y_pred: Optional predicted class (0/1)
    
    Returns:
        Dict with metric names and values
    """
    if y_pred is None:
        y_pred = (y_pred_proba > 0.5).astype(int)
    
    metrics = {
        'auc': roc_auc_score(y_true, y_pred_proba),
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'f1': f1_score(y_true, y_pred, zero_division=0),
        'brier': brier_score_loss(y_true, y_pred_proba),
        'log_loss': log_loss(y_true, y_pred_proba)
    }
    
    return metrics


def train_models(X_train: pd.DataFrame, y_train: pd.Series,
                X_val: pd.DataFrame, y_val: pd.Series,
                sample_weight: Optional[np.ndarray] = None,
                random_state: int = 42) -> Dict[str, Any]:
    """
    Train all three models
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        sample_weight: Optional sample weights
        random_state: Random seed
    
    Returns:
        Dict with trained models
    """
    # Initialize models
    xgb_model = XGBoostRegimeClassifier(random_state=random_state)
    lgb_model = LightGBMRegimeClassifier(random_state=random_state)
    
    # Train models
    print("  Training XGBoost...")
    xgb_model.fit(X_train, y_train, X_val, y_val, sample_weight)
    
    print("  Training LightGBM...")
    lgb_model.fit(X_train, y_train, X_val, y_val, sample_weight)
    
    # Create ensemble
    ensemble = EnsembleRegimeClassifier(xgb_model, lgb_model)
    
    return {
        'xgboost': xgb_model,
        'lightgbm': lgb_model,
        'ensemble': ensemble
    }
