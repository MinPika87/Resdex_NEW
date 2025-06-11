# resdex_agent/memory/session_manager.py
"""
ADK Session Manager for handling session lifecycle and memory integration.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .memory_service import ADKSession, InMemoryMemoryService

logger = logging.getLogger(__name__)


class ADKSessionManager:
    """
    Session Manager following Google ADK patterns for memory integration.
    
    Manages session lifecycle and integration with memory service.
    """
    
    def __init__(self, app_name: str, memory_service: InMemoryMemoryService):
        self.app_name = app_name
        self.memory_service = memory_service
        self.sessions: Dict[str, ADKSession] = {}  # session_id -> ADKSession
        self.user_sessions: Dict[str, Dict[str, ADKSession]] = {}  # user_id -> {session_id -> session}
        
        logger.info(f"ADKSessionManager initialized for app: {app_name}")
        print(f"📝 ADKSessionManager initialized for {app_name}")
    
    async def get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> ADKSession:
        """
        Get existing session or create a new one.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier (generates new if None)
            
        Returns:
            ADKSession object
        """
        try:
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            # Check if session already exists
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.updated_at = datetime.now()
                return session
            
            # Create new session
            session = ADKSession(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            # Store session
            self.sessions[session_id] = session
            
            # Track user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            self.user_sessions[user_id][session_id] = session
            
            logger.info(f"Created new session {session_id} for user {user_id}")
            print(f"📝 Created session {session_id} for user {user_id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get or create session: {e}")
            raise e
    
    async def add_interaction(self, user_id: str, session_id: str, interaction_type: str, content: Any, metadata: Optional[Dict] = None):
        """
        Add an interaction event to a session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            interaction_type: Type of interaction (user_input, search_request, etc.)
            content: Interaction content
            metadata: Optional metadata
        """
        try:
            session = await self.get_or_create_session(user_id, session_id)
            
            # Add event to session
            session.add_event(interaction_type, content, metadata)
            
            logger.debug(f"Added {interaction_type} interaction to session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to add interaction: {e}")
    
    async def update_session_state(self, user_id: str, session_id: str, key: str, value: Any):
        """
        Update session state.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            key: State key
            value: State value
        """
        try:
            session = await self.get_or_create_session(user_id, session_id)
            session.update_state(key, value)
            
            logger.debug(f"Updated session state {key} for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to update session state: {e}")
    
    async def get_session(self, session_id: str) -> Optional[ADKSession]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ADKSession if found, None otherwise
        """
        return self.sessions.get(session_id)
    
    async def get_user_sessions(self, user_id: str) -> Dict[str, ADKSession]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of session_id -> ADKSession
        """
        return self.user_sessions.get(user_id, {})
    
    async def end_session(self, session_id: str):
        """
        Mark a session as ended and optionally save to memory.
        
        Args:
            session_id: Session identifier
        """
        try:
            session = self.sessions.get(session_id)
            if session:
                session.active = False
                session.updated_at = datetime.now()
                
                logger.info(f"Ended session {session_id}")
                print(f"📝 Ended session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
    
    async def save_session_to_memory(self, user_id: str, session_id: str):
        """
        Save a session to long-term memory.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for memory save")
                return
            
            # End the session if still active
            if session.active:
                await self.end_session(session_id)
            
            # Save to memory service
            await self.memory_service.add_session_to_memory(session)
            
            logger.info(f"Saved session {session_id} to memory for user {user_id}")
            print(f"🧠 Saved session {session_id} to memory")
            
        except Exception as e:
            logger.error(f"Failed to save session to memory: {e}")
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        Clean up old inactive sessions.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            sessions_to_remove = []
            
            for session_id, session in self.sessions.items():
                if session.updated_at < cutoff_time and not session.active:
                    sessions_to_remove.append(session_id)
            
            # Remove old sessions
            for session_id in sessions_to_remove:
                session = self.sessions[session_id]
                user_id = session.user_id
                
                # Remove from main sessions dict
                del self.sessions[session_id]
                
                # Remove from user sessions
                if user_id in self.user_sessions and session_id in self.user_sessions[user_id]:
                    del self.user_sessions[user_id][session_id]
                    
                    # Clean up empty user session dicts
                    if not self.user_sessions[user_id]:
                        del self.user_sessions[user_id]
            
            logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
            print(f"🧹 Cleaned up {len(sessions_to_remove)} old sessions")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
    
    async def get_active_sessions(self) -> Dict[str, ADKSession]:
        """
        Get all currently active sessions.
        
        Returns:
            Dictionary of session_id -> ADKSession for active sessions
        """
        return {sid: session for sid, session in self.sessions.items() if session.active}
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.
        
        Returns:
            Dictionary containing session statistics
        """
        try:
            active_sessions = await self.get_active_sessions()
            
            stats = {
                "total_sessions": len(self.sessions),
                "active_sessions": len(active_sessions),
                "total_users": len(self.user_sessions),
                "app_name": self.app_name
            }
            
            # Add user session counts
            user_session_counts = {}
            for user_id, user_sessions in self.user_sessions.items():
                user_session_counts[user_id] = len(user_sessions)
            
            stats["user_session_counts"] = user_session_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {"error": str(e)}
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary containing session summary or None if not found
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                return None
            
            event_types = [event.get("type", "") for event in session.events]
            unique_event_types = list(set(event_types))
            
            duration = (session.updated_at - session.created_at).total_seconds()
            
            return {
                "session_id": session_id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "active": session.active,
                "total_events": len(session.events),
                "event_types": unique_event_types,
                "duration_seconds": duration,
                "app_name": session.app_name,
                "state_keys": list(session.state.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to get session summary: {e}")
            return None
    
    async def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a complete session for backup or analysis.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Complete session data or None if not found
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                return None
            
            return session.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to export session: {e}")
            return None
    
    async def import_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Import a session from exported data.
        
        Args:
            session_data: Session data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_id = session_data.get("session_id")
            user_id = session_data.get("user_id")
            
            if not session_id or not user_id:
                logger.error("Invalid session data: missing session_id or user_id")
                return False
            
            # Create session object
            session = ADKSession(
                app_name=session_data.get("app_name", self.app_name),
                user_id=user_id,
                session_id=session_id
            )
            
            # Restore session properties
            session.events = session_data.get("events", [])
            session.state = session_data.get("state", {})
            session.active = session_data.get("active", False)
            
            # Parse timestamps
            try:
                session.created_at = datetime.fromisoformat(session_data.get("created_at"))
                session.updated_at = datetime.fromisoformat(session_data.get("updated_at"))
            except:
                session.created_at = datetime.now()
                session.updated_at = datetime.now()
            
            # Store session
            self.sessions[session_id] = session
            
            # Track user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            self.user_sessions[user_id][session_id] = session
            
            logger.info(f"Imported session {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import session: {e}")
            return False