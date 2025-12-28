# scripts/orchestrate.py - MAIN PIPELINE ORCHESTRATOR

"""
Astro Finance ML - Complete Pipeline Orchestrator
Runs all data generation in correct sequence
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import Dict, Tuple

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.planetary_data import compute_planetary_positions, save_planetary_data
from scripts.planetary_calendar import detect_major_aspects, predict_next_crash
from scripts.future_predictions import predict_future_90_days
from scripts.yearly_outlook import generate_yearly_outlook

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'
OUTPUT_LOG = PROJECT_ROOT / 'pipeline_results.json'


class PipelineOrchestrator:
    """Orchestrate entire data pipeline"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            'timestamp': self.start_time.isoformat(),
            'stages': {},
            'errors': [],
            'success': False
        }
        
        # Ensure directories exist
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        DATA_RAW.mkdir(parents=True, exist_ok=True)
    
    def log_stage(self, stage_name: str, status: str, message: str = ""):
        """Log stage result"""
        self.results['stages'][stage_name] = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'message': message
        }
        
        if status == 'SUCCESS':
            logger.info(f"✅ {stage_name}: {message}")
        elif status == 'WARNING':
            logger.warning(f"⚠️  {stage_name}: {message}")
        else:
            logger.error(f"❌ {stage_name}: {message}")
            self.results['errors'].append({'stage': stage_name, 'error': message})
    
    def stage_1_planetary_data(self):
        """Stage 1: Compute planetary positions"""
        logger.info("\n" + "="*60)
        logger.info("STAGE 1: COMPUTING PLANETARY POSITIONS")
        logger.info("="*60)
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            df = compute_planetary_positions(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            save_planetary_data(df)
            
            self.log_stage(
                'PLANETARY_DATA',
                'SUCCESS',
                f"Computed {len(df)} days of planetary positions"
            )
            
            return df
            
        except Exception as e:
            self.log_stage('PLANETARY_DATA', 'ERROR', str(e))
            return None
    
    def stage_2_event_calendar(self):
        """Stage 2: Detect planetary events"""
        logger.info("\n" + "="*60)
        logger.info("STAGE 2: DETECTING PLANETARY EVENTS")
        logger.info("="*60)
        
        try:
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            
            events_df = detect_major_aspects(start_date, end_date)
            predict_next_crash(events_df)
            
            self.log_stage(
                'EVENT_CALENDAR',
                'SUCCESS',
                f"Detected {len(events_df)} planetary events"
            )
            
            return events_df
            
        except Exception as e:
            self.log_stage('EVENT_CALENDAR', 'ERROR', str(e))
            return None
    
    def stage_3_future_predictions(self):
        """Stage 3: Generate 90-day predictions"""
        logger.info("\n" + "="*60)
        logger.info("STAGE 3: GENERATING 90-DAY PREDICTIONS")
        logger.info("="*60)
        
        try:
            predictions_df = predict_future_90_days()
            
            self.log_stage(
                'PREDICTIONS',
                'SUCCESS',
                f"Generated {len(predictions_df)} daily predictions"
            )
            
            return predictions_df
            
        except Exception as e:
            self.log_stage('PREDICTIONS', 'ERROR', str(e))
            return None
    
    def stage_4_yearly_outlook(self):
        """Stage 4: Generate yearly outlook"""
        logger.info("\n" + "="*60)
        logger.info("STAGE 4: GENERATING YEARLY OUTLOOK")
        logger.info("="*60)
        
        try:
            outlook = generate_yearly_outlook()
            
            self.log_stage(
                'YEARLY_OUTLOOK',
                'SUCCESS',
                f"Generated 2025 market outlook"
            )
            
            return outlook
            
        except Exception as e:
            self.log_stage('YEARLY_OUTLOOK', 'ERROR', str(e))
            return None
    
    def run_full_pipeline(self):
        """Run complete pipeline"""
        logger.info("\n" + "🚀"*30)
        logger.info("ASTRO FINANCE ML - COMPLETE PIPELINE")
        logger.info("🚀"*30)
        logger.info(f"Started: {self.start_time}")
        logger.info(f"Project: {PROJECT_ROOT}")
        logger.info("")
        
        # Run stages
        df_planetary = self.stage_1_planetary_data()
        df_events = self.stage_2_event_calendar()
        df_predictions = self.stage_3_future_predictions()
        outlook = self.stage_4_yearly_outlook()
        
        # Final summary
        self.finalize()
        
        return df_planetary, df_events, df_predictions, outlook
    
    def finalize(self):
        """Finalize and save results"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.results['end_time'] = end_time.isoformat()
        self.results['duration_seconds'] = duration
        self.results['success'] = len(self.results['errors']) == 0
        
        # Save results
        with open(OUTPUT_LOG, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Log summary
        logger.info("\n" + "="*60)
        logger.info("PIPELINE SUMMARY")
        logger.info("="*60)
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Stages completed: {len(self.results['stages'])}")
        logger.info(f"Errors: {len(self.results['errors'])}")
        logger.info(f"Status: {'✅ SUCCESS' if self.results['success'] else '❌ PARTIAL FAILURE'}")
        logger.info(f"Results saved to: {OUTPUT_LOG}")
        logger.info("")
        
        # Print stage results
        for stage, result in self.results['stages'].items():
            status_emoji = "✅" if result['status'] == 'SUCCESS' else "❌"
            logger.info(f"{status_emoji} {stage}: {result['message']}")
        
        return self.results


def main():
    """Main entry point"""
    orchestrator = PipelineOrchestrator()
    results = orchestrator.run_full_pipeline()
    
    # Exit code
    sys.exit(0 if orchestrator.results['success'] else 1)


if __name__ == '__main__':
    main()
