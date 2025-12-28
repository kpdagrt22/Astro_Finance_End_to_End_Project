# test_db_connection.py - Simple connection test

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from .env
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'pwd')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'planetary_ml')

# Build connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"Attempting to connect with:")
print(f"  Host: {DB_HOST}:{DB_PORT}")
print(f"  User: {DB_USER}")
print(f"  Database: {DB_NAME}")
print(f"  Password: {'*' * len(DB_PASSWORD)}")
print()

try:
    # Create engine
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()
        print("✓ SUCCESS! Connected to PostgreSQL")
        print(f"  Version: {version[0][:50]}...")
        
except Exception as e:
    print(f"✗ FAILED: {e}")
    print()
    print("Troubleshooting:")
    print("1. Is Docker running? Run: docker ps")
    print("2. Is TimescaleDB container up? Run: docker-compose up -d")
    print("3. Is .env password correct? Check docker-compose.yml POSTGRES_PASSWORD")
    print("4. Is port 5432 accessible? Run: netstat -an | findstr 5432")
