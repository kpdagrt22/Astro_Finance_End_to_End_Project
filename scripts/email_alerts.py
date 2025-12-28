# scripts/email_alerts.py - EMAIL ALERT SYSTEM

import logging
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'


def send_crash_alerts(crash_score: int):
    """Send email alerts if crash risk detected"""
    
    if crash_score >= 15:
        alert_level = "🔴 CRITICAL"
        subject = "CRITICAL: Market Crash Alert"
    elif crash_score >= 10:
        alert_level = "🟠 HIGH"
        subject = "WARNING: High Crash Risk"
    else:
        return
    
    logger.info(f"Alert triggered: {alert_level} - Score {crash_score}/20")
    
    # In production: integrate SendGrid, Mailgun, or Twilio
    # For now: just log
    
    alert_data = {
        'timestamp': datetime.now().isoformat(),
        'crash_score': crash_score,
        'level': alert_level,
        'subject': subject
    }
    
    # Save alert history
    alert_file = DATA_PROCESSED / 'alert_history.json'
    history = []
    
    if alert_file.exists():
        with open(alert_file, 'r') as f:
            history = json.load(f)
    
    history.append(alert_data)
    
    with open(alert_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    logger.info(f"Alert saved to: {alert_file}")
