# scripts/planetary_calendar.py - REFINED (ONLY EXACT ASPECTS)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.planetary_data import compute_planetary_positions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_major_aspects(start_date, end_date):
    """Detect major planetary aspects (crash indicators) - EXACT ONLY"""
    
    logger.info("🌙 PLANETARY EVENT CALENDAR (EXACT ASPECTS ONLY)")
    logger.info("=" * 60)
    
    # Compute positions
    df = compute_planetary_positions(start_date, end_date)
    df['date'] = pd.to_datetime(df['date'])
    df = df.reset_index(drop=True)
    
    events = []
    
    # Pre-compute all aspect angles
    aspect_pairs = [
        ('saturn', 'pluto', 0, 'CRITICAL', 'Saturn-Pluto Conjunction', 'MAJOR MARKET CRASH RISK'),
        ('saturn', 'uranus', 90, 'HIGH', 'Saturn-Uranus Square', 'MODERATE CORRECTION RISK'),
        ('jupiter', 'saturn', 0, 'HIGH', 'Jupiter-Saturn Conjunction', 'MAJOR TREND SHIFT (20-yr cycle)'),
        ('jupiter', 'pluto', 0, 'MEDIUM', 'Jupiter-Pluto Conjunction', 'WEALTH/POWER RESTRUCTURING'),
        ('mars', 'saturn', 90, 'MEDIUM', 'Mars-Saturn Square', 'MARKET FRUSTRATION/DELAYS'),
    ]
    
    # Check conjunctions/squares between major planets
    for p1, p2, target_angle, severity, event_name, impact in aspect_pairs:
        lon1_col = f'{p1}_longitude'
        lon2_col = f'{p2}_longitude'
        
        if lon1_col in df.columns and lon2_col in df.columns:
            df['angle_temp'] = np.minimum(
                abs(df[lon1_col] - df[lon2_col]) % 360,
                360 - abs(df[lon1_col] - df[lon2_col]) % 360
            )
            
            # For squares, check angle near 90°
            if target_angle == 90:
                df['in_orb'] = (df['angle_temp'] >= 85) & (df['angle_temp'] <= 95)
            else:  # Conjunctions (0°)
                df['in_orb'] = df['angle_temp'] < 5
            
            # Find exact moments (when aspect becomes exact - minimum angle)
            for idx in range(1, len(df)-1):
                if df.loc[idx, 'in_orb']:
                    prev_angle = df.loc[idx-1, 'angle_temp'] if target_angle == 0 else abs(df.loc[idx-1, 'angle_temp'] - 90)
                    curr_angle = df.loc[idx, 'angle_temp'] if target_angle == 0 else abs(df.loc[idx, 'angle_temp'] - 90)
                    next_angle = df.loc[idx+1, 'angle_temp'] if target_angle == 0 else abs(df.loc[idx+1, 'angle_temp'] - 90)
                    
                    # Local minimum = exact aspect
                    if curr_angle <= prev_angle and curr_angle <= next_angle:
                        events.append({
                            'date': df.loc[idx, 'date'],
                            'event': event_name,
                            'severity': severity,
                            'exactness': f"{curr_angle:.2f}°",
                            'impact': impact
                        })
    
    # Retrograde periods (only start dates)
    retrograde_planets = ['mercury', 'venus', 'mars', 'jupiter', 'saturn']
    retrograde_impacts = {
        'mercury': ('LOW', 'Communication/tech volatility'),
        'venus': ('MEDIUM', 'Financial sector stress (rare)'),
        'mars': ('MEDIUM', 'Market aggression/volatility'),
        'jupiter': ('LOW', 'Economic expansion pause'),
        'saturn': ('HIGH', 'Structural market weakness')
    }
    
    for planet in retrograde_planets:
        lon_col = f'{planet}_longitude'
        if lon_col in df.columns:
            df['velocity'] = df[lon_col].diff()
            df['is_rx'] = df['velocity'] < 0
            
            # Find retrograde start (direction changes)
            for idx in range(2, len(df)):
                if df.loc[idx, 'is_rx'] and not df.loc[idx-1, 'is_rx']:
                    severity, impact = retrograde_impacts.get(planet, ('LOW', 'Market uncertainty'))
                    events.append({
                        'date': df.loc[idx, 'date'],
                        'event': f'{planet.title()} Retrograde Starts',
                        'severity': severity,
                        'exactness': 'Station',
                        'impact': impact
                    })
                elif not df.loc[idx, 'is_rx'] and df.loc[idx-1, 'is_rx']:
                    events.append({
                        'date': df.loc[idx, 'date'],
                        'event': f'{planet.title()} Direct (Rx ends)',
                        'severity': 'LOW',
                        'exactness': 'Station',
                        'impact': 'Volatility eases'
                    })
    
    # New/Full Moons (eclipses possible)
    if 'sun_longitude' in df.columns and 'moon_longitude' in df.columns:
        df['sun_moon_angle'] = np.minimum(
            abs(df['sun_longitude'] - df['moon_longitude']) % 360,
            360 - abs(df['sun_longitude'] - df['moon_longitude']) % 360
        )
        
        # Find exact New Moons (conjunction)
        for idx in range(1, len(df)-1):
            curr = df.loc[idx, 'sun_moon_angle']
            prev = df.loc[idx-1, 'sun_moon_angle']
            next_val = df.loc[idx+1, 'sun_moon_angle']
            
            if curr < 5 and curr <= prev and curr <= next_val:
                events.append({
                    'date': df.loc[idx, 'date'],
                    'event': 'New Moon (Eclipse Window)',
                    'severity': 'MEDIUM',
                    'exactness': f"{curr:.2f}°",
                    'impact': 'New trend initiation'
                })
        
        # Find exact Full Moons (opposition)
        df['opposition_angle'] = abs(df['sun_moon_angle'] - 180)
        for idx in range(1, len(df)-1):
            curr = df.loc[idx, 'opposition_angle']
            prev = df.loc[idx-1, 'opposition_angle']
            next_val = df.loc[idx+1, 'opposition_angle']
            
            if curr < 5 and curr <= prev and curr <= next_val:
                events.append({
                    'date': df.loc[idx, 'date'],
                    'event': 'Full Moon (Eclipse Window)',
                    'severity': 'MEDIUM',
                    'exactness': f"{180 - curr:.2f}°",
                    'impact': 'Sentiment climax/reversal'
                })
    
    events_df = pd.DataFrame(events)
    
    if not events_df.empty:
        events_df = events_df.drop_duplicates(subset=['date', 'event'])
        events_df = events_df.sort_values('date').reset_index(drop=True)
    
    events_df.to_csv('planetary_events_calendar.csv', index=False)
    
    logger.info(f"✓ Detected {len(events_df)} EXACT planetary events")
    
    if not events_df.empty:
        logger.info(f"\nSeverity Breakdown:")
        logger.info(f"  CRITICAL: {(events_df['severity']=='CRITICAL').sum()}")
        logger.info(f"  HIGH:     {(events_df['severity']=='HIGH').sum()}")
        logger.info(f"  MEDIUM:   {(events_df['severity']=='MEDIUM').sum()}")
        logger.info(f"  LOW:      {(events_df['severity']=='LOW').sum()}")
    else:
        logger.info("  No major events in this period")
    
    return events_df

def predict_next_crash(events_df):
    """Predict next major market crash"""
    
    if events_df.empty:
        logger.info("\n✅ No critical crash signals in next 365 days")
        return
    
    today = datetime.now().date()
    events_df['date'] = pd.to_datetime(events_df['date'])
    future_events = events_df[events_df['date'].dt.date > today]
    
    critical = future_events[future_events['severity'] == 'CRITICAL']
    high = future_events[future_events['severity'] == 'HIGH']
    
    logger.info("\n" + "=" * 60)
    logger.info("🚨 CRASH RISK ASSESSMENT")
    logger.info("=" * 60)
    
    if not critical.empty:
        next_critical = critical.iloc[0]
        days_until = (next_critical['date'].date() - today).days
        logger.info(f"⚠️  CRITICAL CRASH SIGNAL:")
        logger.info(f"   📅 Date: {next_critical['date'].date()}")
        logger.info(f"   🌙 Event: {next_critical['event']}")
        logger.info(f"   🎯 Exactness: {next_critical['exactness']}")
        logger.info(f"   💥 Impact: {next_critical['impact']}")
        logger.info(f"   ⏰ Days Until: {days_until}")
        logger.info(f"\n   🚨 RECOMMENDATION: REDUCE EXPOSURE / HEDGE PORTFOLIO")
    elif not high.empty:
        next_high = high.iloc[0]
        days_until = (next_high['date'].date() - today).days
        logger.info(f"⚠️  HIGH-RISK EVENT:")
        logger.info(f"   📅 Date: {next_high['date'].date()}")
        logger.info(f"   🌙 Event: {next_high['event']}")
        logger.info(f"   🎯 Exactness: {next_high['exactness']}")
        logger.info(f"   💥 Impact: {next_high['impact']}")
        logger.info(f"   ⏰ Days Until: {days_until}")
        logger.info(f"\n   ⚠️  RECOMMENDATION: CAUTION / WATCH CLOSELY")
    else:
        logger.info("✅ No critical crash signals detected")
        logger.info("   Market conditions: FAVORABLE for long positions")

if __name__ == "__main__":
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
    
    events_df = detect_major_aspects(start_date, end_date)
    predict_next_crash(events_df)
    
    if not events_df.empty:
        print("\n📅 UPCOMING MAJOR EVENTS (Next 15):")
        print("=" * 80)
        print(events_df.head(15)[['date', 'event', 'severity', 'exactness', 'impact']].to_string(index=False))
        
        # Summary stats
        print(f"\n📊 1-YEAR OUTLOOK SUMMARY:")
        print(f"   Total Events: {len(events_df)}")
        print(f"   Critical: {(events_df['severity']=='CRITICAL').sum()}")
        print(f"   High Risk: {(events_df['severity']=='HIGH').sum()}")
        print(f"   Retrogrades: {events_df['event'].str.contains('Retrograde').sum()}")
        print(f"   Eclipses: {events_df['event'].str.contains('Moon').sum()}")
    else:
        print("\n✅ Calm planetary period - no major crash indicators")
