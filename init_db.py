"""
Database initialization script for PostgreSQL
Creates sample Spider dataset tables and inserts data
"""
import os
import json
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection with fallback logic"""
    # Check if we're in a deployment environment
    is_deployment = os.getenv('STREAMLIT_SHARING') == 'true' or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('VERCEL')
    
    # Try PostgreSQL first (Supabase)
    database_url = os.getenv('DATABASE_URL')
    if database_url and not is_deployment:
        try:
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            logger.info("Connected to PostgreSQL (Supabase)")
            return conn, 'postgresql'
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
    
    # Fallback to SQLite
    if is_deployment:
        # Use in-memory database for deployment
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        logger.info("Using in-memory SQLite for deployment")
        return conn, 'sqlite_memory'
    else:
        # Use file-based SQLite for local development
        db_path = 'spider_demo.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logger.info(f"Using SQLite database: {db_path}")
        return conn, 'sqlite'

def load_spider_schema():
    """Load Spider dataset schema from tables.json"""
    tables_path = os.path.join('spider', 'evaluation_examples', 'examples', 'tables.json')
    
    if not os.path.exists(tables_path):
        logger.error(f"Spider tables.json not found at {tables_path}")
        return []
    
    try:
        with open(tables_path, 'r', encoding='utf-8') as f:
            databases = json.load(f)
        logger.info(f"Loaded {len(databases)} databases from Spider dataset")
        return databases
    except Exception as e:
        logger.error(f"Error loading Spider schema: {e}")
        return []

def get_sql_type(column_type, db_type):
    """Convert Spider column types to SQL types"""
    type_mapping = {
        'postgresql': {
            'text': 'VARCHAR(255)',
            'number': 'INTEGER',
            'time': 'TIMESTAMP',
            'boolean': 'BOOLEAN',
            'others': 'TEXT'
        },
        'sqlite': {
            'text': 'TEXT',
            'number': 'INTEGER',
            'time': 'TEXT',
            'boolean': 'INTEGER',
            'others': 'TEXT'
        }
    }
    
    mapping = type_mapping.get(db_type, type_mapping['sqlite'])
    return mapping.get(column_type, mapping['others'])

def create_database_schema(conn, db_type, database_info):
    """Create tables for a single database"""
    cursor = conn.cursor()
    db_id = database_info['db_id']
    
    try:
        # Get table information
        table_names = database_info['table_names_original']
        column_names = database_info['column_names_original']
        column_types = database_info['column_types']
        primary_keys = database_info.get('primary_keys', [])
        foreign_keys = database_info.get('foreign_keys', [])
        
        # Create tables
        for table_idx, table_name in enumerate(table_names):
            # Clean table name for SQL
            clean_table_name = f"{db_id}_{table_name}".replace(' ', '_').replace('-', '_').lower()
            
            # Get columns for this table
            table_columns = []
            for col_idx, (tbl_idx, col_name) in enumerate(column_names):
                if tbl_idx == table_idx:
                    col_type = column_types[col_idx] if col_idx < len(column_types) else 'text'
                    sql_type = get_sql_type(col_type, db_type)
                    
                    # Clean column name
                    clean_col_name = col_name.replace(' ', '_').replace('-', '_').lower()
                    
                    # Check if this is a primary key
                    is_primary = (col_idx in primary_keys)
                    
                    if db_type == 'postgresql':
                        if is_primary:
                            if sql_type == 'INTEGER':
                                column_def = f"{clean_col_name} SERIAL PRIMARY KEY"
                            else:
                                column_def = f"{clean_col_name} {sql_type} PRIMARY KEY"
                        else:
                            column_def = f"{clean_col_name} {sql_type}"
                    else:  # SQLite
                        if is_primary:
                            column_def = f"{clean_col_name} {sql_type} PRIMARY KEY"
                        else:
                            column_def = f"{clean_col_name} {sql_type}"
                    
                    table_columns.append(column_def)
            
            if table_columns:
                # Create table SQL
                columns_sql = ',\n    '.join(table_columns)
                create_sql = f"""
                CREATE TABLE IF NOT EXISTS {clean_table_name} (
                    {columns_sql}
                );
                """
                
                cursor.execute(create_sql)
                logger.info(f"Created table: {clean_table_name}")
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error creating schema for {db_id}: {e}")
        conn.rollback()
        return False

def insert_sample_data(conn, db_type, database_info):
    """Insert sample data for demonstration"""
    cursor = conn.cursor()
    db_id = database_info['db_id']
    
    try:
        # Sample data for popular databases
        sample_data = {
            'concert_singer': {
                f'{db_id}_stadium': [
                    (1, 'Rosemont', 'Allstate Arena', 18500, 20000, 10000, 15000),
                    (2, 'Phoenix', 'Talking Stick Resort Arena', 18422, 19000, 9000, 14000),
                    (3, 'Anaheim', 'Honda Center', 17174, 18000, 8000, 13000)
                ],
                f'{db_id}_singer': [
                    (1, 'John Mayer', 'United States', 'Gravity', 2006, 45, 1),
                    (2, 'Taylor Swift', 'United States', 'Love Story', 2008, 34, 0),
                    (3, 'Ed Sheeran', 'United Kingdom', 'Shape of You', 2017, 33, 1)
                ],
                f'{db_id}_concert': [
                    (1, 'Summer Music Festival', 'Pop', 1, 2023),
                    (2, 'Rock Night', 'Rock', 2, 2023),
                    (3, 'Acoustic Evening', 'Acoustic', 3, 2024)
                ]
            },
            'student_transcripts_tracking': {
                f'{db_id}_students': [
                    (1, 'John', 'Doe', 'john.doe@email.com', '2000-01-15'),
                    (2, 'Jane', 'Smith', 'jane.smith@email.com', '1999-05-20'),
                    (3, 'Mike', 'Johnson', 'mike.j@email.com', '2001-03-10')
                ],
                f'{db_id}_courses': [
                    (1, 'Computer Science', 'CS101'),
                    (2, 'Mathematics', 'MATH201'),
                    (3, 'Physics', 'PHYS101')
                ]
            },
            'world_1': {
                f'{db_id}_country': [
                    ('AFG', 'Afghanistan', 'Asia', 'Southern and Central Asia', 652090, 1919, 22720000, 45.9, 5976, None, 'Afganistan/Afqanestan', 'Islamic Emirate', 'Mohammad Omar', 1, 'AF'),
                    ('USA', 'United States', 'North America', 'North America', 9363520, 1776, 278357000, 78.3, 8510700, 8110900, 'United States', 'Federal Republic', 'George W. Bush', 3813, 'US'),
                    ('KOR', 'South Korea', 'Asia', 'Eastern Asia', 99720, 1948, 46844000, 74.4, 320749, 442544, 'Taehan Min\'guk (South Korea)', 'Republic', 'Kim Dae-jung', 2331, 'KR')
                ],
                f'{db_id}_city': [
                    (1, 'Kabul', 'AFG', 'Kabol', 1780000),
                    (2, 'New York', 'USA', 'New York', 8008278),
                    (3, 'Seoul', 'KOR', 'Seoul', 9981619)
                ]
            }
        }
        
        # Insert sample data if available for this database
        if db_id in sample_data:
            for table_name, rows in sample_data[db_id].items():
                if rows:
                    # Get column count for this table
                    if db_type == 'postgresql':
                        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position")
                    else:
                        cursor.execute(f"PRAGMA table_info({table_name})")
                    
                    columns = cursor.fetchall()
                    if columns:
                        col_count = len(columns)
                        placeholders = ', '.join(['%s' if db_type == 'postgresql' else '?' for _ in range(col_count)])
                        
                        insert_sql = f"INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})" if db_type == 'sqlite' else f"INSERT INTO {table_name} VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                        
                        for row in rows:
                            try:
                                cursor.execute(insert_sql, row[:col_count])
                            except Exception as e:
                                logger.warning(f"Could not insert sample data into {table_name}: {e}")
        
        conn.commit()
        logger.info(f"Inserted sample data for {db_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error inserting sample data for {db_id}: {e}")
        conn.rollback()
        return False

def init_database():
    """Initialize database with all Spider datasets"""
    conn, db_type = get_db_connection()
    
    try:
        # Load Spider schema
        databases = load_spider_schema()
        
        if not databases:
            logger.error("No Spider databases found")
            return False
        
        logger.info(f"Initializing {len(databases)} databases...")
        
        # Create schemas for all databases (limit to first 10 for demo)
        success_count = 0
        for i, db_info in enumerate(databases[:10]):  # Limit for demo
            db_id = db_info['db_id']
            logger.info(f"Processing database {i+1}/{min(10, len(databases))}: {db_id}")
            
            if create_database_schema(conn, db_type, db_info):
                insert_sample_data(conn, db_type, db_info)
                success_count += 1
            
        logger.info(f"Successfully initialized {success_count} databases")
        
        # Create a summary table for easy reference
        cursor = conn.cursor()
        
        if db_type == 'postgresql':
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS database_summary (
                    id SERIAL PRIMARY KEY,
                    db_id VARCHAR(100),
                    table_count INTEGER,
                    description TEXT
                );
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS database_summary (
                    id INTEGER PRIMARY KEY,
                    db_id TEXT,
                    table_count INTEGER,
                    description TEXT
                );
            """)
        
        # Insert database summaries
        for db_info in databases[:10]:
            db_id = db_info['db_id']
            table_count = len(db_info['table_names'])
            description = f"Database with {table_count} tables: {', '.join(db_info['table_names'][:3])}{'...' if table_count > 3 else ''}"
            
            if db_type == 'postgresql':
                cursor.execute(
                    "INSERT INTO database_summary (db_id, table_count, description) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    (db_id, table_count, description)
                )
            else:
                cursor.execute(
                    "INSERT OR IGNORE INTO database_summary (db_id, table_count, description) VALUES (?, ?, ?)",
                    (db_id, table_count, description)
                )
        
        conn.commit()
        logger.info("Database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
    finally:
        conn.close()

def get_available_databases():
    """Get list of available databases"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT db_id, table_count, description FROM database_summary ORDER BY db_id")
        databases = cursor.fetchall()
        return [dict(db) for db in databases]
    except Exception as e:
        logger.error(f"Error getting database list: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Initializing Spider dataset databases...")
    
    if init_database():
        print("✅ Database initialization completed!")
        print("\n📊 Available databases:")
        
        databases = get_available_databases()
        for db in databases:
            print(f"  - {db['db_id']}: {db['description']}")
        
        print(f"\n🎯 Total: {len(databases)} databases ready to use!")
        print("\n💡 You can now ask questions about any of these databases!")
        print("   Examples:")
        print("   - 'Show me all tables in concert_singer database'")
        print("   - 'What countries are in the world_1 database?'")
        print("   - 'List all students in student_transcripts_tracking'")
    else:
        print("❌ Database initialization failed!")
