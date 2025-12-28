# services/email_service.py - Email Integration
from database.db_manager import DatabaseManager

def subscribe_user(email):
    """Subscribe user to email list"""
    if not email or '@' not in email:
        return False
    
    db = DatabaseManager()
    return db.add_subscriber(email)

def send_crash_alert(email, crash_score):
    """Send crash alert email"""
    # In production: Use SendGrid/Mailgun API
    # For now, just log
    print(f"Sending alert to {email}: Score {crash_score}")
