# scripts/train_models.py - FIXED (feature_cols scope issue)

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import joblib
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# scripts/train_models.py - UPDATED PATHS

import pandas as pd
from pathlib import Path

# Define paths
DATA_DIR = Path(__file__).parent.parent / 'data' / 'processed'
MODEL_DIR = Path(__file__).parent.parent / 'models'

# Load features
print("Loading features...")
features_full = pd.read_parquet(DATA_DIR / 'features_full.parquet')
features_selected = pd.read_parquet(DATA_DIR / 'features_selected.parquet')

# Train models
# ... your training code ...

# Save models
import joblib
joblib.dump(xgb_model, MODEL_DIR / 'xgboost_model.pkl')
print(f"✅ Model saved to {MODEL_DIR / 'xgboost_model.pkl'}")

def load_features():
    """Load feature datasets"""
    logger.info("Loading feature datasets...")
    
    df = pd.read_parquet('features_selected.parquet')
    df['date'] = pd.to_datetime(df['date'])
    
    logger.info(f"✓ Loaded {len(df):,} rows × {len(df.columns):,} features")
    logger.info(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    
    return df.sort_values('date')

def prepare_data(df):
    """Prepare data for ML models"""
    logger.info("Preparing data for ML...")
    
    target_col = 'djia_fwd_direction_5d'
    if target_col not in df.columns:
        logger.error(f"Target {target_col} not found!")
        return None, None, None, None, None, None
    
    feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                   if not col.startswith('dxy_fwd') and not col.startswith('djia_fwd') 
                   and not col.startswith('gold_fwd') and col != target_col]
    
    X = df[feature_cols].fillna(method='ffill').fillna(0)
    y = df[target_col].fillna(0)
    
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    logger.info(f"✓ Training: {len(X_train):,} samples, Test: {len(X_test):,} samples")
    logger.info(f"✓ Features: {len(feature_cols)}")
    logger.info(f"Target balance: {y_train.mean():.1%} UP / {1-y_train.mean():.1%} DOWN")
    
    return X_train_scaled, X_test_scaled, y_train.values, y_test.values, scaler, feature_cols

def train_xgboost(X_train, X_test, y_train, y_test, feature_cols):
    """Train XGBoost classifier"""
    logger.info("\n" + "="*60)
    logger.info("TRAINING XGBOOST")
    logger.info("="*60)
    
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"✅ XGBoost Accuracy: {accuracy:.3f}")
    
    # Feature importance
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False).head(20)
    
    logger.info("\nTop 10 XGBoost Features:")
    for i, row in importance_df.head(10).iterrows():
        logger.info(f"  {i+1:2d}. {row['feature'][:30]:30s} {row['importance']:.4f}")
    
    Path('models').mkdir(exist_ok=True)
    joblib.dump(model, 'models/xgboost_model.pkl')
    joblib.dump(importance_df, 'models/xgboost_importance.pkl')
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=importance_df.head(15), x='importance', y='feature')
    plt.title('XGBoost Top 15 Feature Importance')
    plt.tight_layout()
    plt.savefig('models/xgboost_importance.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return model, y_pred, y_pred_proba, accuracy

def train_lstm(X_train, X_test, y_train, y_test, scaler, feature_cols):
    """Train LSTM neural network"""
    logger.info("\n" + "="*60)
    logger.info("TRAINING LSTM")
    logger.info("="*60)
    
    timesteps = 30
    X_train_lstm = []
    X_test_lstm = []
    
    for i in range(timesteps, len(X_train)):
        X_train_lstm.append(X_train[i-timesteps:i])
    for i in range(timesteps, len(X_test)):
        X_test_lstm.append(X_test[i-timesteps:i])
    
    X_train_lstm = np.array(X_train_lstm)
    X_test_lstm = np.array(X_test_lstm)
    y_train_lstm = y_train[timesteps:]
    y_test_lstm = y_test[timesteps:]
    
    logger.info(f"LSTM shape: Train {X_train_lstm.shape}, Test {X_test_lstm.shape}")
    
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(timesteps, X_train.shape[1])),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dropout(0.1),
        Dense(1, activation='sigmoid')
    ])
    
    model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])
    
    history = model.fit(
        X_train_lstm, y_train_lstm,
        epochs=50, batch_size=32, verbose=0,
        validation_split=0.1,
        callbacks=[tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)]
    )
    
    y_pred_proba = model.predict(X_test_lstm, verbose=0).flatten()
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    accuracy = accuracy_score(y_test_lstm, y_pred)
    logger.info(f"✅ LSTM Accuracy: {accuracy:.3f}")
    
    Path('models').mkdir(exist_ok=True)
    model.save('models/lstm_model.h5')
    joblib.dump(scaler, 'models/lstm_scaler.pkl')
    
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Val Loss')
    plt.title('LSTM Training Loss')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Train Acc')
    plt.plot(history.history['val_accuracy'], label='Val Acc')
    plt.title('LSTM Training Accuracy')
    plt.legend()
    plt.tight_layout()
    plt.savefig('models/lstm_training_history.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return model, y_pred, y_pred_proba, accuracy

def create_ensemble_predictions(xgb_pred, xgb_proba, lstm_pred, lstm_proba):
    """Simple ensemble averaging"""
    logger.info("\n" + "="*60)
    logger.info("CREATING ENSEMBLE PREDICTIONS")
    logger.info("="*60)
    
    min_len = min(len(xgb_pred), len(lstm_pred))
    ensemble_proba = (xgb_proba[:min_len] + lstm_proba[:min_len]) / 2
    ensemble_pred = (ensemble_proba > 0.5).astype(int)
    
    return ensemble_pred, ensemble_proba

def evaluate_models(y_test, xgb_pred, lstm_pred, ensemble_pred):
    """Comprehensive model evaluation"""
    logger.info("\n" + "="*60)
    logger.info("MODEL EVALUATION SUMMARY")
    logger.info("="*60)
    
    results = {}
    
    for name, pred in [('XGBoost', xgb_pred), ('LSTM', lstm_pred), ('Ensemble', ensemble_pred)]:
        acc = accuracy_score(y_test, pred)
        results[name] = acc
        logger.info(f"{name:10s}: {acc:.3f} ({acc*100:.1f}%)")
    
    # Confusion matrices
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
    
    for i, (name, pred) in enumerate([('XGBoost', xgb_pred), ('LSTM', lstm_pred), ('Ensemble', ensemble_pred)]):
        cm = confusion_matrix(y_test, pred)
        disp = ConfusionMatrixDisplay(cm, display_labels=['DOWN', 'UP'])
        disp.plot(ax=axes[i], cmap='Blues')
        axes[i].set_title(f'{name} (Acc: {results[name]:.3f})')
    
    plt.tight_layout()
    plt.savefig('models/model_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return results

def main():
    """Complete ML training pipeline"""
    Path('models').mkdir(exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("🚀 PHASE 3: ML MODEL TRAINING (XGBoost + LSTM + Ensemble)")
    logger.info("=" * 80)
    
    df = load_features()
    X_train, X_test, y_train, y_test, scaler, feature_cols = prepare_data(df)
    
    if X_train is None:
        logger.error("Data preparation failed!")
        return
    
    # Train XGBoost
    xgb_model, xgb_pred, xgb_proba, xgb_acc = train_xgboost(X_train, X_test, y_train, y_test, feature_cols)
    
    # Train LSTM
    lstm_model, lstm_pred, lstm_proba, lstm_acc = train_lstm(X_train, X_test, y_train, y_test, scaler, feature_cols)
    
    # Ensemble
    ensemble_pred, ensemble_proba = create_ensemble_predictions(xgb_pred, xgb_proba, lstm_pred, lstm_proba)
    
    # Evaluate
    min_len = len(ensemble_pred)
    results = evaluate_models(y_test[:min_len], xgb_pred[:min_len], lstm_pred[:min_len], ensemble_pred)
    
    # Save predictions
    predictions_df = pd.DataFrame({
        'xgb_proba': xgb_proba,
        'lstm_proba': np.pad(lstm_proba, (0, len(xgb_proba)-len(lstm_proba))),
        'ensemble_proba': np.pad(ensemble_proba, (0, len(xgb_proba)-len(ensemble_proba))),
        'xgb_pred': xgb_pred,
        'lstm_pred': np.pad(lstm_pred, (0, len(xgb_pred)-len(lstm_pred))),
        'ensemble_pred': np.pad(ensemble_pred, (0, len(xgb_pred)-len(ensemble_pred))),
        'true': y_test
    })
    predictions_df.to_csv('models/predictions.csv', index=False)
    
    logger.info("\n" + "=" * 80)
    logger.info("🎉 PHASE 3 COMPLETE - PRODUCTION MODELS READY!")
    logger.info("=" * 80)
    logger.info("📁 Saved:")
    logger.info("  • models/xgboost_model.pkl")
    logger.info("  • models/lstm_model.h5") 
    logger.info("  • models/lstm_scaler.pkl")
    logger.info("  • models/predictions.csv")
    logger.info("  • models/*.png (charts)")
    
    best_model = max(results.items(), key=lambda x: x[1])
    logger.info(f"\n🏆 BEST: {best_model[0]} ({best_model[1]:.3f})")
    
    logger.info("\n🚀 PRODUCTION READY!")
    logger.info("📈 Next: python scripts/live_predictions.py")

if __name__ == "__main__":
    main()
