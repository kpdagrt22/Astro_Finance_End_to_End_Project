"""
Simple Pipeline Runner - Manual Execution
Runs Phase 2 feature engineering, labeling, and model training
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("="*70)
print("NAVAGRAHA ML PIPELINE - PHASE 2")
print("="*70)

# ============================================================================
# STEP 1: LOAD DATA FROM PHASE 1
# ============================================================================
print("\n[1/6] Loading planetary events data...")
events_df = pd.read_csv('data/processed/drikpanchang/events_all_planets_merged.csv')
print(f"  ✓ Loaded {len(events_df)} planetary events")

# ============================================================================
# STEP 2: GENERATE FEATURES
# ============================================================================
print("\n[2/6] Generating Navagraha features...")
from features.navagraha_features import build_feature_matrix

features_df = build_feature_matrix(
    events_df=events_df,
    start_date='1900-01-01',
    end_date='2025-12-31',
    include_interactions=True,
    include_stability_metrics=True,
    include_advanced_features=True,
    include_dasha_cycles=True
)

print(f"  ✓ Generated {features_df.shape[1]} features for {features_df.shape[0]} days")

# Save features
features_df.to_csv('results/features_navagraha.csv')
print(f"  ✓ Saved to: results/features_navagraha.csv")

# ============================================================================
# STEP 3: LOAD PRICE DATA AND GENERATE LABELS
# ============================================================================
print("\n[3/6] Generating market regime labels...")

# Load S&P 500 prices (you need this file)
try:
    prices_df = pd.read_csv('data/sp500_prices.csv', index_col='date', parse_dates=True)
except:
    print("  ⚠️  Price data not found. Creating dummy data for testing...")
    # Create dummy price data for testing
    dates = pd.date_range('1900-01-01', '2025-12-31', freq='D')
    prices_df = pd.DataFrame({
        'close': np.random.randn(len(dates)).cumsum() + 100
    }, index=dates)

from labels.label_engine import generate_labels

labels_df = generate_labels(
    price_df=prices_df,
    events_df=events_df,
    strategies=['drawdown', 'volatility', 'event', 'combined'],
    drawdown_threshold=0.10,
    volatility_threshold=0.02,
    event_window_days=30
)

print(f"  ✓ Generated labels: {labels_df.shape}")

# Save labels
labels_df.to_csv('results/labels_navagraha.csv')
print(f"  ✓ Saved to: results/labels_navagraha.csv")

# ============================================================================
# STEP 4: MERGE FEATURES AND LABELS
# ============================================================================
print("\n[4/6] Merging features and labels...")

# Align indices
merged_df = features_df.join(labels_df['label_combined'], how='inner')
print(f"  ✓ Merged shape: {merged_df.shape}")

# Split X and y
X = merged_df.iloc[:, :-1]
y = merged_df.iloc[:, -1]

print(f"  Features (X): {X.shape}")
print(f"  Labels (y): {y.shape}")
print(f"  Label distribution: {y.value_counts().to_dict()}")

# ============================================================================
# STEP 5: RUN WALK-FORWARD VALIDATION
# ============================================================================
print("\n[5/6] Running walk-forward validation...")

from models.validation import run_walk_forward_validation, summarize_metrics

# Class weights
class_weights = {0: 1.0, 1: 15.0}

metrics_df = run_walk_forward_validation(
    X=X,
    y=y,
    class_weights=class_weights,
    train_years=50,
    test_years=5,
    stride_years=5,
    random_state=42
)

# Save metrics
metrics_df.to_csv('results/model_metrics.csv', index=False)
print(f"  ✓ Saved metrics to: results/model_metrics.csv")

# ============================================================================
# STEP 6: SUMMARIZE RESULTS
# ============================================================================
print("\n[6/6] Generating summary...")

summary_df = summarize_metrics(metrics_df)
print("\n" + "="*70)
print("FINAL RESULTS")
print("="*70)
print(summary_df)

# Save summary
summary_df.to_csv('results/model_summary.csv')
print(f"\n✓ Saved summary to: results/model_summary.csv")

# Check if target achieved
ensemble_auc = summary_df.loc['ensemble', 'auc_mean']
target_auc = 0.72

print("\n" + "="*70)
if ensemble_auc >= target_auc:
    print(f"🎉 SUCCESS! Target AUC achieved: {ensemble_auc:.4f} >= {target_auc}")
else:
    print(f"⚠️  Target not met: {ensemble_auc:.4f} < {target_auc}")
print("="*70)

print(f"\n✓ Pipeline completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("✓ All results saved to: results/")
