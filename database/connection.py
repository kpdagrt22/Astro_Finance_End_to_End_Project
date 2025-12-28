# database/connection.py - Initialize TimescaleDB with correct schema

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'astro_finance')}"

def get_engine():
    """Get database engine"""
    return create_engine(DATABASE_URL, echo=False)

def init_database():
    """Initialize database with all tables and hypertables"""
    engine = get_engine()
    
    logger.info("✓ Testing database connection...")
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False
    
    # Drop and recreate tables with EXACT schema from planetary_data.py
    logger.info("Creating tables...")
    
    # Financial data table
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS financial_data CASCADE;
            CREATE TABLE financial_data (
                date TIMESTAMPTZ NOT NULL,
                symbol TEXT NOT NULL,
                open DOUBLE PRECISION,
                high DOUBLE PRECISION,
                low DOUBLE PRECISION,
                close DOUBLE PRECISION,
                volume BIGINT
            );
            SELECT create_hypertable('financial_data', 'date');
            CREATE INDEX ON financial_data (symbol, date DESC);
        """))
    
    # Planetary positions table - EXACT 32 columns from your data
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS planetary_positions CASCADE;
            CREATE TABLE planetary_positions (
                date TIMESTAMPTZ NOT NULL,
                sun_longitude DOUBLE PRECISION,
                sun_latitude DOUBLE PRECISION,
                sun_declination DOUBLE PRECISION,
                moon_longitude DOUBLE PRECISION,
                moon_latitude DOUBLE PRECISION,
                moon_declination DOUBLE PRECISION,
                moon_phase DOUBLE PRECISION,
                mercury_longitude DOUBLE PRECISION,
                mercury_latitude DOUBLE PRECISION,
                mercury_declination DOUBLE PRECISION,
                venus_longitude DOUBLE PRECISION,
                venus_latitude DOUBLE PRECISION,
                venus_declination DOUBLE PRECISION,
                mars_longitude DOUBLE PRECISION,
                mars_latitude DOUBLE PRECISION,
                mars_declination DOUBLE PRECISION,
                jupiter_longitude DOUBLE PRECISION,
                jupiter_latitude DOUBLE PRECISION,
                jupiter_declination DOUBLE PRECISION,
                saturn_longitude DOUBLE PRECISION,
                saturn_latitude DOUBLE PRECISION,
                saturn_declination DOUBLE PRECISION,
                uranus_longitude DOUBLE PRECISION,
                uranus_latitude DOUBLE PRECISION,
                uranus_declination DOUBLE PRECISION,
                neptune_longitude DOUBLE PRECISION,
                neptune_latitude DOUBLE PRECISION,
                neptune_declination DOUBLE PRECISION,
                pluto_longitude DOUBLE PRECISION,
                pluto_latitude DOUBLE PRECISION,
                pluto_declination DOUBLE PRECISION
            );
            SELECT create_hypertable('planetary_positions', 'date');
            CREATE INDEX ON planetary_positions (date DESC);
        """))
    
    # Future tables
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS planetary_aspects CASCADE;
            CREATE TABLE planetary_aspects (
                date TIMESTAMPTZ NOT NULL,
                planet1 TEXT NOT NULL,
                planet2 TEXT NOT NULL,
                aspect_type TEXT NOT NULL,
                angle DOUBLE PRECISION,
                orb DOUBLE PRECISION,
                is_exact BOOLEAN
            );
            SELECT create_hypertable('planetary_aspects', 'date');
            
            DROP TABLE IF EXISTS predictions CASCADE;
            CREATE TABLE predictions (
                date TIMESTAMPTZ NOT NULL,
                symbol TEXT NOT NULL,
                horizon INTEGER NOT NULL,
                prediction DOUBLE PRECISION,
                confidence DOUBLE PRECISION,
                direction INTEGER,
                model_version TEXT,
                sharpe_ratio DOUBLE PRECISION
            );
            SELECT create_hypertable('predictions', 'date');
        """))
    
    logger.info("✓ All tables created successfully")
    logger.info("✓ TimescaleDB hypertables ready")
    return True

# Export engine for other modules
engine = get_engine()

if __name__ == "__main__":
    success = init_database()
    if success:
        logger.info("\n✓ DATABASE SETUP COMPLETE")
        logger.info("Run: python scripts/download_data.py")
    else:
        logger.error("✗ Database setup failed")
