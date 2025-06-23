# In resdex_agent/utils/db_manager.py

import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
from typing import Dict, List, Optional, Any
import logging
from ..config import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database operations manager with enhanced compatibility."""
    
    def __init__(self):
        db_config = config.database
        
        # FIXED: More explicit connection string format
        self.connection_params = {
            'host': db_config.host.split(':')[0],  # Extract host without port
            'port': int(db_config.host.split(':')[1]) if ':' in db_config.host else 3306,
            'user': db_config.user,
            'password': db_config.password,
            'database': db_config.database,
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        # Create connection string without schema parameter
        self.connection_string = (
            f'mysql+pymysql://{self.connection_params["user"]}:'
            f'{self.connection_params["password"]}@'
            f'{self.connection_params["host"]}:'
            f'{self.connection_params["port"]}/'
            f'{self.connection_params["database"]}'
            f'?charset={self.connection_params["charset"]}'
        )
        
        print(f"💾 DATABASE MANAGER INITIALIZED:")
        print(f"  - Host: {self.connection_params['host']}:{self.connection_params['port']}")
        print(f"  - User: {self.connection_params['user']}")
        print(f"  - Database: {self.connection_params['database']}")
    
    def get_connection(self):
        """Create database connection with enhanced error handling."""
        try:
            print(f"🔌 CREATING DATABASE CONNECTION...")
            
            # FIXED: Create engine with explicit parameters
            engine = create_engine(
                self.connection_string,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            
            # Test the connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            print(f"✅ Database engine created and tested successfully")
            return engine
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            print(f"❌ Database connection failed: {e}")
            return None
    
    async def get_real_names(self, user_ids: List[str]) -> Dict[str, str]:
        """Fetch real names with enhanced error handling and fallback methods."""
        if not user_ids:
            return {}
        
        try:
            engine = self.get_connection()
            if not engine:
                print("❌ Failed to connect to database")
                return {}
            
            print(f"🔍 Fetching real names for {len(user_ids)} users from database...")
            print(f"🔍 Sample user IDs: {user_ids[:5]}")
            
            # Convert to string format for SQL
            user_ids_str = ",".join([str(uid) for uid in user_ids])
            
            # FIXED: Use text() for raw SQL to avoid pandas/SQLAlchemy conflicts
            query = text(f"""
                SELECT userid, name
                FROM UserDetails 
                WHERE userid IN ({user_ids_str})
            """)
            
            print(f"  - Executing query...")
            
            # FIXED: Use direct connection instead of pandas read_sql
            name_mapping = {}
            
            with engine.connect() as conn:
                result = conn.execute(query)
                rows = result.fetchall()
                
                print(f"✅ DATABASE QUERY SUCCESSFUL:")
                print(f"  - UserDetails table returned {len(rows)} matching rows")
                
                # Create mapping dictionary
                for row in rows:
                    user_id = int(row[0])  # userid
                    name = str(row[1]).strip() if row[1] else None  # name
                    
                    if name and name != 'None' and name != '' and name.lower() != 'null':
                        name_mapping[user_id] = name
            
            print(f"✅ Successfully created name mapping for {len(name_mapping)} users")
            
            if len(name_mapping) > 0:
                print(f"🔍 Sample name mappings: {dict(list(name_mapping.items())[:3])}")
            else:
                print(f"⚠️ No valid names found in database")
            
            return name_mapping
            
        except Exception as e:
            logger.error(f"Database error in get_real_names: {e}")
            print(f"❌ Database error in get_real_names: {e}")
            import traceback
            traceback.print_exc()
            
            # FALLBACK: Try alternative query method
            try:
                return await self._fallback_name_query(user_ids, engine)
            except Exception as fallback_error:
                print(f"❌ Fallback query also failed: {fallback_error}")
                return {}
    
    async def _fallback_name_query(self, user_ids: List[str], engine) -> Dict[str, str]:
        """Fallback method using chunked queries."""
        print(f"🔄 ATTEMPTING FALLBACK NAME QUERY...")
        
        name_mapping = {}
        chunk_size = 20  # Smaller chunks
        
        for i in range(0, len(user_ids), chunk_size):
            chunk = user_ids[i:i + chunk_size]
            chunk_str = ",".join([str(uid) for uid in chunk])
            
            try:
                query = text(f"SELECT userid, name FROM UserDetails WHERE userid IN ({chunk_str}) AND name IS NOT NULL AND name != ''")
                
                with engine.connect() as conn:
                    result = conn.execute(query)
                    rows = result.fetchall()
                    
                    for row in rows:
                        user_id = int(row[0])
                        name = str(row[1]).strip()
                        if name and name != 'None' and name.lower() != 'null':
                            name_mapping[user_id] = name
                            
                print(f"✅ Chunk {i//chunk_size + 1}: Found {len([r for r in rows if r[1]])} names")
                
            except Exception as chunk_error:
                print(f"❌ Chunk {i//chunk_size + 1} failed: {chunk_error}")
                continue
        
        print(f"🔄 FALLBACK COMPLETE: {len(name_mapping)} total names found")
        return name_mapping
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test database connection with enhanced diagnostics."""
        try:
            print(f"🧪 TESTING DATABASE CONNECTION...")
            
            engine = self.get_connection()
            if not engine:
                return {"success": False, "error": "Failed to create database engine"}
            
            # Test basic connectivity
            with engine.connect() as conn:
                # Test 1: Basic connection
                result = conn.execute(text("SELECT 1 as test"))
                test_row = result.fetchone()
                print(f"  ✅ Basic connectivity: {test_row[0]}")
                
                # Test 2: Database access
                result = conn.execute(text("SELECT DATABASE() as current_db"))
                db_row = result.fetchone()
                print(f"  ✅ Current database: {db_row[0]}")
                
                # Test 3: Table existence
                result = conn.execute(text("SHOW TABLES LIKE 'UserDetails'"))
                table_row = result.fetchone()
                table_exists = table_row is not None
                print(f"  ✅ UserDetails table exists: {table_exists}")
                
                # Test 4: Count rows
                if table_exists:
                    result = conn.execute(text("SELECT COUNT(*) as count FROM UserDetails LIMIT 1"))
                    count_row = result.fetchone()
                    row_count = count_row[0] if count_row else 0
                    print(f"  ✅ UserDetails row count: {row_count:,}")
                else:
                    row_count = 0
                
                # Test 5: Sample name query
                if table_exists and row_count > 0:
                    result = conn.execute(text("SELECT userid, name FROM UserDetails WHERE name IS NOT NULL AND name != '' LIMIT 3"))
                    sample_rows = result.fetchall()
                    print(f"  ✅ Sample names: {len(sample_rows)} found")
                    for row in sample_rows:
                        print(f"    - User {row[0]}: {row[1]}")
            
            return {
                "success": True,
                "message": "Database connection successful",
                "details": {
                    "table_exists": table_exists,
                    "row_count": row_count,
                    "connection_params": {
                        "host": self.connection_params['host'],
                        "port": self.connection_params['port'],
                        "database": self.connection_params['database']
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            print(f"❌ Database test failed: {e}")
            return {
                "success": False, 
                "error": f"Database test failed: {e}",
                "connection_string": self.connection_string.replace(self.connection_params['password'], '***')
            }
    
    def chunk(self, lst, chunk_size):
        """Split list into chunks of specified size"""
        if hasattr(lst, 'tolist'):
            lst = lst.tolist()
        chunks = []
        for i in range(0, len(lst), chunk_size):
            chunks.append(lst[i:i + chunk_size])
        return chunks


# Global database manager instance
db_manager = DatabaseManager()  