# Replace resdx_agent/utils/db_manager.py with this fixed version

"""
Database management utilities.
"""

import pandas as pd #type: ignore
import pymysql #type: ignore
from sqlalchemy import create_engine #type: ignore
from typing import Dict, List, Optional, Any
import logging
from ..config import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database operations manager."""
    
    def __init__(self):
        db_config = config.database
        self.connection_string = f'mysql+pymysql://{db_config.user}:{db_config.password}@{db_config.host}/{db_config.database}'
        print(f"💾 DATABASE MANAGER INITIALIZED:")
        print(f"  - Host: {db_config.host}")
        print(f"  - User: {db_config.user}")
        print(f"  - Database: {db_config.database}")
        print(f"  - Connection string: mysql+pymysql://{db_config.user}:***@{db_config.host}/{db_config.database}")
    
    def get_connection(self):
        """Create database connection."""
        try:
            print(f"🔌 CREATING DATABASE CONNECTION...")
            db_connection = create_engine(self.connection_string)
            print(f"✅ Database engine created successfully")
            return db_connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            print(f"❌ Database connection failed: {e}")
            return None
    
    def chunk(self, lst, chunk_size):
        """Split list into chunks of specified size"""
        if hasattr(lst, 'tolist'):
            lst = lst.tolist()
        chunks = []
        for i in range(0, len(lst), chunk_size):
            chunks.append(lst[i:i + chunk_size])
        return chunks
    
    async def get_real_names(self, user_ids: List[str]) -> Dict[str, str]:
        """Fetch real names for given user IDs from database using working version logic."""
        if not user_ids:
            return {}
        
        try:
            db_connection = self.get_connection()
            if not db_connection:
                print("❌ Failed to connect to database")
                return {}
            
            print(f"🔍 Fetching real names for {len(user_ids)} users from database...")
            print(f"🔍 Sample user IDs: {user_ids[:5]}")
            
            # Convert to string format for SQL
            user_ids_str = ",".join([str(uid) for uid in user_ids])
            
            # Use the working version query format
            query = f"""
                SELECT userid, name
                FROM UserDetails 
                WHERE userid IN ({user_ids_str})
            """
            
            print(f"  - Test query: {query[:100]}...")
            
            df = pd.read_sql(query, con=db_connection)
            
            print(f"✅ DATABASE TEST SUCCESSFUL:")
            print(f"  - UserDetails table has {len(df)} matching rows")
            
            # Create mapping dictionary using working version logic
            name_mapping = {}
            for _, row in df.iterrows():
                user_id = int(row['userid'])
                name = str(row['name']).strip()
                if name and name != 'None' and name != '':
                    name_mapping[user_id] = name
            
            print(f"✅ Successfully created name mapping for {len(name_mapping)} users")
            print(f"🔍 Sample name mappings: {dict(list(name_mapping.items())[:3])}")
            
            return name_mapping
            
        except Exception as e:
            logger.error(f"Database error in get_real_names: {e}")
            print(f"❌ Database error in get_real_names: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test database connection and return info."""
        try:
            print(f"🧪 TESTING DATABASE CONNECTION...")
            db_connection = self.get_connection()
            if not db_connection:
                return {"success": False, "error": "Failed to connect to database"}
            
            test_query = "SELECT COUNT(*) as count FROM UserDetails LIMIT 1"
            print(f"  - Test query: {test_query}")
            df = pd.read_sql(test_query, con=db_connection)
            
            row_count = df.iloc[0]['count'] if not df.empty else 0
            print(f"✅ DATABASE TEST SUCCESSFUL:")
            print(f"  - UserDetails table has {row_count} rows")
            
            return {
                "success": True,
                "message": "Database connection successful",
                "row_count": row_count
            }
            
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            return {"success": False, "error": f"Database test failed: {e}"}


# Global database manager instance
db_manager = DatabaseManager()