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
    
    def get_connection(self):
        """Create database connection."""
        try:
            return create_engine(self.connection_string)
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    async def get_real_names(self, user_ids: List[str]) -> Dict[str, str]:
        """Fetch real names for given user IDs."""
        if not user_ids:
            return {}
        
        try:
            db_connection = self.get_connection()
            if not db_connection:
                return {}
            
            # Convert to string format for SQL
            user_ids_str = ",".join([str(uid) for uid in user_ids])
            
            query = f"""
                SELECT userid, name
                FROM UserDetails 
                WHERE userid IN ({user_ids_str})
            """
            
            df = pd.read_sql(query, con=db_connection)
            
            # Create mapping dictionary
            name_mapping = {}
            for _, row in df.iterrows():
                user_id = int(row['userid'])
                name = str(row['name']).strip()
                if name and name != 'None' and name != '':
                    name_mapping[user_id] = name
            
            logger.info(f"Retrieved {len(name_mapping)} real names from database")
            return name_mapping
            
        except Exception as e:
            logger.error(f"Database error in get_real_names: {e}")
            return {}
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test database connection and return info."""
        try:
            db_connection = self.get_connection()
            if not db_connection:
                return {"success": False, "error": "Failed to connect to database"}
            
            test_query = "SELECT COUNT(*) as count FROM UserDetails LIMIT 1"
            df = pd.read_sql(test_query, con=db_connection)
            
            return {
                "success": True,
                "message": "Database connection successful",
                "row_count": df.iloc[0]['count'] if not df.empty else 0
            }
            
        except Exception as e:
            return {"success": False, "error": f"Database test failed: {e}"}


# Global database manager instance
db_manager = DatabaseManager()