# scripts/email_alerts.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_daily_crash_alert(user_email, crash_score, next_event):
    """Send daily crash risk alerts to subscribers"""
    
    if crash_score >= 10:  # Only send if HIGH risk
        subject = f"🚨 CRASH ALERT: Risk Score {crash_score}/20"
        
        body = f"""
        🌙 Astro Finance ML - Daily Alert
        
        ⚠️ CURRENT CRASH RISK: {crash_score}/20
        
        📅 Next Major Event: {next_event['event']}
        📆 Date: {next_event['date']}
        ⏰ Days Until: {next_event['days_until']}
        
        💡 Recommendation: Reduce equity exposure to 40-50%
        
        View full analysis: https://yourdomain.com
        
        Unsubscribe: https://yourdomain.com/unsubscribe
        """
        
        # Send email (use SendGrid or Mailgun for free tier)
        # Implementation here
