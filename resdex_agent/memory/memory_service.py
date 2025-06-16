# resdex_agent/memory/memory_service.py
"""
In-Memory Memory Service implementation following Google ADK patterns.
"""

import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)


class MemoryResult:
    """Represents a single memory search result following ADK patterns."""
    
    def __init__(self, content: str, session_id: str, timestamp: str, score: float = 1.0, metadata: Optional[Dict] = None):
        self.content = content
        self.session_id = session_id
        self.timestamp = timestamp
        self.score = score
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "content": self.content,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "score": self.score,
            "metadata": self.metadata
        }


class SearchMemoryResponse:
    """Response object for memory search operations following ADK patterns."""
    
    def __init__(self, results: List[MemoryResult], query: str, total_found: int):
        self.results = results
        self.query = query
        self.total_found = total_found
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "results": [result.to_dict() for result in self.results],
            "query": self.query,
            "total_found": self.total_found
        }


class ADKSession:
    """Simplified ADK Session representation for memory integration."""
    
    def __init__(self, app_name: str, user_id: str, session_id: str):
        self.app_name = app_name
        self.user_id = user_id
        self.session_id = session_id
        self.events = []
        self.state = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.active = True
    
    def add_event(self, event_type: str, content: Any, metadata: Optional[Dict] = None):
        """Add an event to the session."""
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id
        }
        self.events.append(event)
        self.updated_at = datetime.now()
    
    def update_state(self, key: str, value: Any):
        """Update session state."""
        self.state[key] = value
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "app_name": self.app_name,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "events": self.events,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "active": self.active
        }


class InMemoryMemoryService:
    """
    In-Memory Memory Service following Google ADK patterns.
    
    This implementation stores session information in memory and performs
    keyword-based searching for memory retrieval.
    
    Note: All data is lost when the application restarts.
    """
    
    def __init__(self):
        self.memory_store: Dict[str, List[Dict[str, Any]]] = {}  # user_id -> list of memory entries
        self.session_cache: Dict[str, ADKSession] = {}  # session_id -> session
        self.created_at = datetime.now()
        
        logger.info("InMemoryMemoryService initialized")
        print("🧠 InMemoryMemoryService initialized - ADK compatible")
    
    async def add_session_to_memory(self, session: ADKSession) -> "InMemoryMemoryService":
        """
        Add a session to long-term memory following ADK patterns.
        
        Args:
            session: ADKSession object containing events and state
            
        Returns:
            Self for method chaining
        """
        try:
            user_id = session.user_id
            
            # Initialize user memory if not exists
            if user_id not in self.memory_store:
                self.memory_store[user_id] = []
            
            # Extract meaningful information from session events
            memory_entries = self._extract_memory_from_session(session)
            
            # Add to user's memory store
            self.memory_store[user_id].extend(memory_entries)
            
            # Keep only recent entries to prevent unbounded growth
            self._trim_user_memory(user_id, max_entries=100)
            
            logger.info(f"Added session {session.session_id} to memory for user {user_id}")
            print(f"🧠 Added {len(memory_entries)} memory entries from session {session.session_id}")
            
            return self
            
        except Exception as e:
            logger.error(f"Failed to add session to memory: {e}")
            raise e
    
    async def search_memory(self, app_name: str, user_id: str, query: str, max_results: int = 10) -> SearchMemoryResponse:
        """
        Search memory for relevant information following ADK patterns.
        
        Args:
            app_name: Application name (for filtering if needed)
            user_id: User identifier
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            SearchMemoryResponse containing relevant memory results
        """
        try:
            print(f"🔍 Searching memory for user {user_id} with query: '{query}'")
            
            # Get user's memory entries
            user_memories = self.memory_store.get(user_id, [])
            
            if not user_memories:
                print(f"📭 No memories found for user {user_id}")
                return SearchMemoryResponse(results=[], query=query, total_found=0)
            
            # Perform keyword-based search
            scored_results = self._search_memories(user_memories, query)
            
            # Sort by relevance score and limit results
            scored_results.sort(key=lambda x: x.score, reverse=True)
            top_results = scored_results[:max_results]
            
            print(f"📚 Found {len(top_results)} relevant memories from {len(user_memories)} total")
            
            return SearchMemoryResponse(
                results=top_results,
                query=query,
                total_found=len(scored_results)
            )
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return SearchMemoryResponse(results=[], query=query, total_found=0)
    
    def _extract_memory_from_session(self, session: ADKSession) -> List[Dict[str, Any]]:
        memory_entries = []
        
        try:
            # Process each event in the session
            for event in session.events:
                memory_entry = self._create_memory_entry_from_event(event, session)
                if memory_entry:
                    memory_entries.append(memory_entry)
            
            # ENHANCED: Add session summary with better context
            if session.events:
                summary_entry = self._create_enhanced_session_summary_entry(session)
                if summary_entry:
                    memory_entries.append(summary_entry)
            
        except Exception as e:
            logger.error(f"Failed to extract memory from session: {e}")
        
        return memory_entries
    
    def _create_memory_entry_from_event(self, event: Dict[str, Any], session: ADKSession) -> Optional[Dict[str, Any]]:
        """Create a memory entry from a session event."""
        try:
            event_type = event.get("type", "")
            content = event.get("content", {})
            
            # Skip system events that aren't user-relevant
            skip_types = ["system_status", "health_check", "debug"]
            if event_type in skip_types:
                return None
            
            # Create searchable text content
            searchable_content = self._create_searchable_content(event_type, content)
            
            if not searchable_content:
                return None
            
            return {
                "id": event.get("id", str(uuid.uuid4())),
                "type": event_type,
                "content": searchable_content,
                "original_content": content,
                "session_id": session.session_id,
                "user_id": session.user_id,
                "timestamp": event.get("timestamp", datetime.now().isoformat()),
                "app_name": session.app_name,
                "keywords": self._extract_keywords(searchable_content),
                "metadata": event.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to create memory entry from event: {e}")
            return None
    
    def _create_searchable_content(self, event_type: str, content: Any) -> str:
        """Create searchable text content from event data."""
        try:
            if isinstance(content, str):
                return content
            
            if isinstance(content, dict):
                searchable_parts = []
                
                # Handle different event types
                if event_type == "user_input":
                    user_message = content.get("message", "")
                    if user_message:
                        searchable_parts.append(f"User asked: {user_message}")
                
                elif event_type == "search_request":
                    query = content.get("query", "")
                    if query:
                        searchable_parts.append(f"Search for: {query}")
                    
                    # Add filter information
                    session_state = content.get("session_state", {})
                    keywords = session_state.get("keywords", [])
                    if keywords:
                        searchable_parts.append(f"Skills: {', '.join(keywords)}")
                
                elif event_type == "candidate_search":
                    filters = content.get("filters", {})
                    keywords = filters.get("keywords", [])
                    if keywords:
                        searchable_parts.append(f"Searched candidates with skills: {', '.join(keywords)}")
                
                elif event_type == "search_results":
                    candidates_found = content.get("candidates_found", 0)
                    total_count = content.get("total_count", 0)
                    searchable_parts.append(f"Found {candidates_found} candidates from {total_count} total matches")
                
                elif event_type == "general_response":
                    query = content.get("query", "")
                    response = content.get("response", "")
                    if query:
                        searchable_parts.append(f"Discussed: {query}")
                    if response and len(response) < 200:  # Include short responses
                        searchable_parts.append(f"Response: {response}")
                
                # Generic handling for other content
                for key, value in content.items():
                    if isinstance(value, str) and len(value) < 500 and key not in ["session_state", "metadata"]:
                        searchable_parts.append(f"{key}: {value}")
                
                return " | ".join(searchable_parts)
            
            return str(content)[:500]  # Limit length
            
        except Exception as e:
            logger.error(f"Failed to create searchable content: {e}")
            return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for better searching."""
        try:
            # Simple keyword extraction
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were"}
            words = text.lower().split()
            keywords = []
            
            for word in words:
                # Clean word
                clean_word = ''.join(c for c in word if c.isalnum())
                if clean_word and len(clean_word) > 2 and clean_word not in stop_words:
                    keywords.append(clean_word)
            
            return list(set(keywords))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            return []
    
    def _create_enhanced_session_summary_entry(self, session: ADKSession) -> Optional[Dict[str, Any]]:
        try:
            if not session.events:
                return None
            
            # Extract meaningful information from events
            user_messages = []
            assistant_responses = []
            search_queries = []
            user_name = None
            
            for event in session.events:
                content = event.get("content", {})
                event_type = event.get("type", "")
                
                if event_type == "user_input":
                    message = content.get("message", "")
                    if message:
                        user_messages.append(message)
                        # Extract name if mentioned
                        if "my name is" in message.lower():
                            import re
                            name_match = re.search(r'my name is (\w+)', message.lower())
                            if name_match:
                                user_name = name_match.group(1).title()
                
                elif event_type == "assistant_response":
                    response = content.get("message", "")
                    if response:
                        assistant_responses.append(response[:100])
                
                elif event_type == "search_request":
                    query = content.get("query", "")
                    if query:
                        search_queries.append(query)
            
            # Create comprehensive summary
            summary_parts = []
            summary_parts.append(f"Session with {len(session.events)} interactions")
            
            if user_name:
                summary_parts.append(f"User name: {user_name}")
            
            if user_messages:
                summary_parts.append(f"User discussed: {', '.join(user_messages[:3])}")
            
            if search_queries:
                summary_parts.append(f"Searched for: {', '.join(search_queries[:2])}")
            
            summary_content = " | ".join(summary_parts)
            
            return {
                "id": f"enhanced_summary_{session.session_id}",
                "type": "enhanced_session_summary",
                "content": summary_content,
                "original_content": {
                    "session_id": session.session_id,
                    "event_count": len(session.events),
                    "user_name": user_name,
                    "user_messages": user_messages[:5],  # Keep last 5
                    "search_queries": search_queries[:3],  # Keep last 3
                    "duration": (session.updated_at - session.created_at).total_seconds()
                },
                "session_id": session.session_id,
                "user_id": session.user_id,
                "timestamp": session.updated_at.isoformat(),
                "app_name": session.app_name,
                "keywords": self._extract_keywords(summary_content),
                "metadata": {"is_enhanced_summary": True, "user_name": user_name}
            }
            
        except Exception as e:
            logger.error(f"Failed to create enhanced session summary: {e}")
            return None
    
    def _search_memories(self, memories: List[Dict[str, Any]], query: str) -> List[MemoryResult]:
        try:
            query_keywords = self._extract_keywords(query.lower())
            if not query_keywords:
                # If no keywords, return recent memories
                return self._get_recent_memories(memories, limit=5)
            
            results = []
            
            for memory in memories:
                score = self._calculate_intelligent_relevance_score(memory, query_keywords, query)
                if score > 0:  # Only include relevant results
                    result = MemoryResult(
                        content=memory.get("content", ""),
                        session_id=memory.get("session_id", ""),
                        timestamp=memory.get("timestamp", ""),
                        score=score,
                        metadata=memory.get("metadata", {})
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    def _calculate_intelligent_relevance_score(self, memory: Dict[str, Any], query_keywords: List[str], original_query: str) -> float:
        try:
            memory_keywords = memory.get("keywords", [])
            memory_content = memory.get("content", "").lower()
            original_content = memory.get("original_content", {})
            
            if not memory_keywords and not memory_content:
                return 0.0
            
            score = 0.0
            
            # 1. Direct keyword matching
            for query_kw in query_keywords:
                for memory_kw in memory_keywords:
                    if query_kw in memory_kw or memory_kw in query_kw:
                        score += 1.0
                
                # Direct content matching
                if query_kw in memory_content:
                    score += 0.7
            
            # 2. Intelligent context matching
            if "name" in original_query.lower():
                # Boost memories that contain name information
                if "name" in memory_content or "my name is" in memory_content:
                    score += 2.0
                if isinstance(original_content, dict) and original_content.get("user_name"):
                    score += 3.0  # High boost for memories with extracted names
            
            # 3. Content type relevance
            memory_type = memory.get("type", "")
            if memory_type == "user_input" and len(query_keywords) > 0:
                score += 0.5  # Boost user inputs for general queries
            elif memory_type == "session_summary":
                score += 0.3  # Moderate boost for summaries
            
            # 4. Recency boost (more recent = higher score)
            try:
                memory_time = datetime.fromisoformat(memory.get("timestamp", ""))
                age_hours = (datetime.now() - memory_time).total_seconds() / 3600
                if age_hours < 1:  # Very recent
                    score += 0.5
                elif age_hours < 24:  # Recent
                    score += 0.3
                elif age_hours < 168:  # This week
                    score += 0.1
            except:
                pass
            
            # 5. Content quality boost
            content_length = len(memory_content)
            if 20 <= content_length <= 200:  # Ideal length
                score += 0.2
            
            return score
            
        except Exception as e:
            logger.error(f"Failed to calculate relevance score: {e}")
            return 0.0
    
    def _get_recent_memories(self, memories: List[Dict[str, Any]], limit: int = 5) -> List[MemoryResult]:
        """Get recent memories when no specific query."""
        try:
            # Sort by timestamp and return recent ones
            sorted_memories = sorted(
                memories, 
                key=lambda x: x.get("timestamp", ""), 
                reverse=True
            )
            
            results = []
            for memory in sorted_memories[:limit]:
                result = MemoryResult(
                    content=memory.get("content", ""),
                    session_id=memory.get("session_id", ""),
                    timestamp=memory.get("timestamp", ""),
                    score=0.5,  # Default score for recent memories
                    metadata=memory.get("metadata", {})
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get recent memories: {e}")
            return []
    def _trim_user_memory(self, user_id: str, max_entries: int = 500):
        """Trim user memory to prevent unbounded growth."""
        try:
            if user_id not in self.memory_store:
                return
            
            memories = self.memory_store[user_id]
            if len(memories) > max_entries:
                # Sort by timestamp (newest first) and keep only the most recent
                memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                self.memory_store[user_id] = memories[:max_entries]
                
                logger.info(f"Trimmed user {user_id} memory to {max_entries} entries")
            
        except Exception as e:
            logger.error(f"Failed to trim user memory: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory service statistics."""
        try:
            total_entries = sum(len(memories) for memories in self.memory_store.values())
            total_users = len(self.memory_store)
            
            return {
                "type": "InMemoryMemoryService",
                "total_users": total_users,
                "total_entries": total_entries,
                "created_at": self.created_at.isoformat(),
                "uptime_hours": (datetime.now() - self.created_at).total_seconds() / 3600
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}
    
    def clear_user_memory(self, user_id: str):
        """Clear all memory for a specific user."""
        try:
            if user_id in self.memory_store:
                del self.memory_store[user_id]
                logger.info(f"Cleared memory for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to clear user memory: {e}")
    
    def clear_all_memory(self):
        """Clear all memory (use with caution)."""
        try:
            self.memory_store.clear()
            self.session_cache.clear()
            logger.info("Cleared all memory")
        except Exception as e:
            logger.error(f"Failed to clear all memory: {e}")