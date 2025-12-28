# scripts/yearly_outlook.py - FULL YEAR PLANETARY MARKET ANALYSIS (FIXED)

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.planetary_data import compute_planetary_positions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_yearly_outlook(year=2025):
    """Complete planetary analysis for given year"""
    
    logger.info(f"📅 {year} MARKET OUTLOOK (Planetary Analysis)")
    logger.info("=" * 60)
    
    # Compute full year planetary data
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    df = compute_planetary_positions(start_date, end_date)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    
    # Analyze key patterns
    outlook = {}
    
    # 1. Mercury Retrograde Periods (volatility)
    if 'mercury_longitude' in df.columns:
        df['mercury_velocity'] = df['mercury_longitude'].diff()
        df['mercury_rx'] = df['mercury_velocity'] < 0
        mercury_rx_days = df[df['mercury_rx']].groupby(
            (df['mercury_rx'] != df['mercury_rx'].shift()).cumsum()
        )['date'].agg(['min', 'max', 'count'])
        mercury_rx_days = mercury_rx_days[mercury_rx_days['count'] > 5]  # Filter noise
        
        # Convert to serializable format
        rx_periods = []
        for idx, row in mercury_rx_days.iterrows():
            rx_periods.append({
                'start': row['min'].strftime('%Y-%m-%d'),
                'end': row['max'].strftime('%Y-%m-%d'),
                'days': int(row['count'])
            })
        
        outlook['mercury_retrograde'] = {
            'periods': len(mercury_rx_days),
            'total_days': int(mercury_rx_days['count'].sum()),
            'dates': rx_periods
        }
        
        logger.info(f"\n🌑 Mercury Retrograde ({len(mercury_rx_days)} periods):")
        for period in rx_periods:
            logger.info(f"   {period['start']} to {period['end']} ({period['days']} days)")
    
    # 2. Major Outer Planet Aspects (crashes/rallies)
    major_aspects = []
    planets = ['jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
    
    for i, p1 in enumerate(planets):
        for p2 in planets[i+1:]:
            lon1_col = f'{p1}_longitude'
            lon2_col = f'{p2}_longitude'
            
            if lon1_col in df.columns and lon2_col in df.columns:
                df['angle'] = np.minimum(
                    abs(df[lon1_col] - df[lon2_col]) % 360,
                    360 - abs(df[lon1_col] - df[lon2_col]) % 360
                )
                
                # Conjunction (0°)
                conjunctions = df[df['angle'] < 5]
                if not conjunctions.empty:
                    major_aspects.append(f"{p1.title()}-{p2.title()} Conjunction ({len(conjunctions)} days)")
                
                # Opposition (180°)
                oppositions = df[(df['angle'] > 175) & (df['angle'] < 185)]
                if not oppositions.empty:
                    major_aspects.append(f"{p1.title()}-{p2.title()} Opposition ({len(oppositions)} days)")
    
    outlook['major_aspects'] = major_aspects
    logger.info(f"\n🌍 Major Outer Planet Aspects:")
    for aspect in major_aspects[:10]:
        logger.info(f"   • {aspect}")
    
    # 3. Quarterly Outlook
    quarterly_outlook = {}
    for q in [1, 2, 3, 4]:
        q_data = df[df['quarter'] == q]
        
        # Average moon velocity (market sentiment proxy)
        if 'moon_velocity' in q_data.columns:
            avg_moon_vel = float(q_data['moon_velocity'].mean())
        else:
            avg_moon_vel = 0
        
        # Mercury Rx days in quarter
        if 'mercury_rx' in q_data.columns:
            mercury_rx_days_q = int(q_data['mercury_rx'].sum())
        else:
            mercury_rx_days_q = 0
        
        quarterly_outlook[f'Q{q}'] = {
            'sentiment': 'BULLISH' if avg_moon_vel > 0 else 'BEARISH',
            'volatility': 'HIGH' if mercury_rx_days_q > 10 else 'NORMAL',
            'mercury_rx_days': mercury_rx_days_q,
            'avg_moon_velocity': round(avg_moon_vel, 2)
        }
    
    outlook['quarterly'] = quarterly_outlook
    
    logger.info(f"\n📊 Quarterly Breakdown:")
    for q, data in quarterly_outlook.items():
        logger.info(f"   {q}: {data['sentiment']} | Volatility: {data['volatility']} | Mercury Rx: {data['mercury_rx_days']} days")
    
    # 4. Best/Worst Trading Periods
    favorable_windows = []
    if 'saturn_longitude' in df.columns:
        df['saturn_velocity'] = df['saturn_longitude'].diff()
        df['saturn_favorable'] = df['saturn_velocity'] > 0
        
        favorable_periods = df[df['saturn_favorable']].groupby(
            (df['saturn_favorable'] != df['saturn_favorable'].shift()).cumsum()
        )['date'].agg(['min', 'max', 'count'])
        favorable_periods = favorable_periods[favorable_periods['count'] > 30]
        
        logger.info(f"\n✅ Favorable Trading Windows (Saturn Direct):")
        for idx, row in favorable_periods.head(3).iterrows():
            window = {
                'start': row['min'].strftime('%Y-%m-%d'),
                'end': row['max'].strftime('%Y-%m-%d'),
                'days': int(row['count'])
            }
            favorable_windows.append(window)
            logger.info(f"   {window['start']} to {window['end']} ({window['days']} days)")
    
    outlook['favorable_windows'] = favorable_windows
    
    # Save to JSON
    import json
    with open(f'market_outlook_{year}.json', 'w') as f:
        json.dump(outlook, f, indent=2)
    
    logger.info(f"\n✓ Saved outlook to market_outlook_{year}.json")
    
    # Visualization
    create_yearly_chart(df, year)
    
    return outlook

def create_yearly_chart(df, year):
    """Create visual yearly planetary chart"""
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 12))
    
    # Plot 1: Major planet longitudes
    planets = ['jupiter', 'saturn', 'uranus']
    for planet in planets:
        col = f'{planet}_longitude'
        if col in df.columns:
            axes[0].plot(df['date'], df[col], label=planet.title(), linewidth=2)
    axes[0].set_title(f'{year} Outer Planet Positions (Crash Indicators)', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Ecliptic Longitude (°)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Mercury retrograde periods
    if 'mercury_rx' in df.columns:
        axes[1].fill_between(df['date'], 0, 1, where=df['mercury_rx'], alpha=0.3, color='red', label='Mercury Rx')
        axes[1].set_title(f'{year} Mercury Retrograde Periods (Volatility)', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Retrograde')
        axes[1].set_ylim([-0.1, 1.1])
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
    
    # Plot 3: Moon velocity (sentiment proxy)
    if 'moon_velocity' in df.columns:
        df['moon_velocity_smooth'] = df['moon_velocity'].rolling(7).mean()
        axes[2].plot(df['date'], df['moon_velocity_smooth'], color='steelblue', linewidth=2)
        axes[2].axhline(0, color='red', linestyle='--', alpha=0.5)
        axes[2].fill_between(df['date'], 0, df['moon_velocity_smooth'], 
                            where=df['moon_velocity_smooth']>0, alpha=0.3, color='green', label='Bullish')
        axes[2].fill_between(df['date'], 0, df['moon_velocity_smooth'], 
                            where=df['moon_velocity_smooth']<0, alpha=0.3, color='red', label='Bearish')
        axes[2].set_title(f'{year} Market Sentiment (Moon Velocity)', fontsize=14, fontweight='bold')
        axes[2].set_ylabel('Velocity (°/day)')
        axes[2].set_xlabel('Date')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'market_outlook_{year}.png', dpi=300, bbox_inches='tight')
    logger.info(f"✓ Saved chart to market_outlook_{year}.png")
    plt.close()

if __name__ == "__main__":
    outlook = generate_yearly_outlook(2025)
    
    print("\n" + "="*80)
    print(f"📈 2025 MARKET SUMMARY")
    print("="*80)
    
    if 'mercury_retrograde' in outlook:
        print(f"\n🌑 Mercury Retrograde: {outlook['mercury_retrograde']['periods']} periods")
        print(f"   Total Rx Days: {outlook['mercury_retrograde']['total_days']}/365")
    
    if 'quarterly' in outlook:
        print(f"\n📊 Quarterly Sentiment:")
        for q, data in outlook['quarterly'].items():
            print(f"   {q}: {data['sentiment']} ({data['volatility']} volatility)")
    
    if 'favorable_windows' in outlook:
        print(f"\n✅ Best Trading Periods:")
        for window in outlook['favorable_windows']:
            print(f"   {window['start']} to {window['end']} ({window['days']} days)")
    
    print("\n✓ Full analysis saved to:")
    print(f"   📄 market_outlook_2025.json")
    print(f"   📊 market_outlook_2025.png")
