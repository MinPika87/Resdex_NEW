# resdex_agent/tools/memory_tools.py
"""
Memory tools for ResDex Agent following Google ADK patterns.
"""

from typing import Dict, Any, List, Optional
import logging

# Simple Tool base class
class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

from ..memory.memory_service import InMemoryMemoryService, SearchMemoryResponse

logger = logging.getLogger(__name__)


class MemoryTool(Tool):
    """
    Tool for interacting with the memory service following Google ADK patterns.
    
    This tool allows agents to search and retrieve information from long-term memory.
    """
    
    def __init__(self, name: str = "memory_tool", memory_service: Optional[InMemoryMemoryService] = None):
        super().__init__(
            name=name, 
            description="Search and retrieve information from conversation memory"
        )
        self.memory_service = memory_service
        
        if self.memory_service:
            logger.info("MemoryTool initialized with memory service")
            print("🧠 MemoryTool initialized with memory service")
        else:
            logger.warning("MemoryTool initialized without memory service")
    
    async def __call__(self, 
                      user_id: str,
                      query: str,
                      max_results: int = 10,
                      app_name: str = "ResDexRootAgent") -> Dict[str, Any]:
        """
        Search memory for relevant information.
        
        Args:
            user_id: User identifier
            query: Search query string
            max_results: Maximum number of results to return
            app_name: Application name (for filtering if needed)
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            if not self.memory_service:
                return {
                    "success": False,
                    "error": "Memory service not available",
                    "results": [],
                    "total_found": 0
                }
            
            if not user_id or not query:
                return {
                    "success": False,
                    "error": "user_id and query are required",
                    "results": [],
                    "total_found": 0
                }
            
            logger.info(f"Memory search: user={user_id}, query='{query}', max_results={max_results}")
            print(f"🔍 Memory search for user {user_id}: '{query}'")
            
            # Search memory using the memory service
            search_response = await self.memory_service.search_memory(
                app_name=app_name,
                user_id=user_id,
                query=query,
                max_results=max_results
            )
            
            # Convert MemoryResult objects to dictionaries
            results = [result.to_dict() for result in search_response.results]
            
            logger.info(f"Memory search completed: found {len(results)} results")
            print(f"📚 Memory search found {len(results)} results")
            
            return {
                "success": True,
                "results": results,
                "total_found": search_response.total_found,
                "query": search_response.query,
                "user_id": user_id,
                "tool_used": self.name
            }
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            print(f"❌ Memory search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "total_found": 0,
                "query": query,
                "user_id": user_id
            }
    
    async def search_by_type(self, 
                           user_id: str, 
                           interaction_type: str, 
                           max_results: int = 5) -> Dict[str, Any]:
        """
        Search memory for specific interaction types.
        
        Args:
            user_id: User identifier
            interaction_type: Type of interaction to search for
            max_results: Maximum number of results
            
        Returns:
            Dictionary containing search results
        """
        try:
            # Use the interaction type as the search query
            return await self(
                user_id=user_id,
                query=interaction_type,
                max_results=max_results
            )
            
        except Exception as e:
            logger.error(f"Memory search by type failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "total_found": 0
            }
    
    async def get_recent_interactions(self, 
                                    user_id: str, 
                                    hours: int = 24, 
                                    max_results: int = 10) -> Dict[str, Any]:
        """
        Get recent interactions for a user.
        
        Args:
            user_id: User identifier
            hours: Number of hours to look back
            max_results: Maximum number of results
            
        Returns:
            Dictionary containing recent interactions
        """
        try:
            # Search for general interactions (this is a simplified approach)
            # In a more sophisticated implementation, you would filter by timestamp
            search_query = "user interaction search general"
            
            result = await self(
                user_id=user_id,
                query=search_query,
                max_results=max_results
            )
            
            if result["success"]:
                # Filter results by timestamp (simplified - in production you'd want better filtering)
                from datetime import datetime, timedelta
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                recent_results = []
                for memory_result in result["results"]:
                    try:
                        timestamp_str = memory_result.get("timestamp", "")
                        if timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            if timestamp >= cutoff_time:
                                recent_results.append(memory_result)
                    except:
                        # If timestamp parsing fails, include the result anyway
                        recent_results.append(memory_result)
                
                result["results"] = recent_results[:max_results]
                result["total_found"] = len(recent_results)
                result["hours_back"] = hours
            
            return result
            
        except Exception as e:
            logger.error(f"Get recent interactions failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "total_found": 0
            }
    
    async def search_conversations_about(self, 
                                       user_id: str, 
                                       topic: str, 
                                       max_results: int = 5) -> Dict[str, Any]:
        """
        Search for conversations about a specific topic.
        
        Args:
            user_id: User identifier
            topic: Topic to search for
            max_results: Maximum number of results
            
        Returns:
            Dictionary containing conversation results
        """
        try:
            # Enhance the search query for better topic matching
            enhanced_query = f"discussion conversation talk {topic}"
            
            result = await self(
                user_id=user_id,
                query=enhanced_query,
                max_results=max_results
            )
            
            if result["success"]:
                result["topic"] = topic
                result["search_type"] = "conversation"
            
            return result
            
        except Exception as e:
            logger.error(f"Search conversations about '{topic}' failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "total_found": 0,
                "topic": topic
            }
    
    async def search_searches_about(self, 
                                  user_id: str, 
                                  search_criteria: str, 
                                  max_results: int = 5) -> Dict[str, Any]:
        """
        Search for past searches about specific criteria.
        
        Args:
            user_id: User identifier
            search_criteria: Search criteria to look for
            max_results: Maximum number of results
            
        Returns:
            Dictionary containing past search results
        """
        try:
            # Enhance the search query for better search matching
            enhanced_query = f"search candidate filter {search_criteria}"
            
            result = await self(
                user_id=user_id,
                query=enhanced_query,
                max_results=max_results
            )
            
            if result["success"]:
                result["search_criteria"] = search_criteria
                result["search_type"] = "past_search"
            
            return result
            
        except Exception as e:
            logger.error(f"Search past searches about '{search_criteria}' failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "total_found": 0,
                "search_criteria": search_criteria
            }
    
    def get_memory_service_stats(self) -> Dict[str, Any]:
        """
        Get memory service statistics.
        
        Returns:
            Dictionary containing memory service statistics
        """
        try:
            if not self.memory_service:
                return {
                    "success": False,
                    "error": "Memory service not available"
                }
            
            stats = self.memory_service.get_memory_stats()
            stats["success"] = True
            stats["tool_name"] = self.name
            
            return stats
            
        except Exception as e:
            logger.error(f"Get memory service stats failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def clear_user_memory(self, user_id: str) -> Dict[str, Any]:
        """
        Clear all memory for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary indicating success or failure
        """
        try:
            if not self.memory_service:
                return {
                    "success": False,
                    "error": "Memory service not available"
                }
            
            self.memory_service.clear_user_memory(user_id)
            
            logger.info(f"Cleared memory for user {user_id}")
            print(f"🧹 Cleared memory for user {user_id}")
            
            return {
                "success": True,
                "message": f"Cleared all memory for user {user_id}",
                "user_id": user_id,
                "tool_used": self.name
            }
            
        except Exception as e:
            logger.error(f"Clear user memory failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }


class LoadMemoryTool(Tool):
    """
    Alternative memory tool following Google ADK's load_memory pattern.
    
    This provides a simplified interface similar to ADK's built-in load_memory tool.
    """
    
    def __init__(self, name: str = "load_memory", memory_service: Optional[InMemoryMemoryService] = None):
        super().__init__(
            name=name,
            description="Load relevant information from conversation memory"
        )
        self.memory_service = memory_service
        self.memory_tool = MemoryTool("internal_memory_tool", memory_service)
    
    async def __call__(self, 
                      query: str,
                      user_id: str = "default_user",
                      max_results: int = 5) -> Dict[str, Any]:
        """
        Load memory following ADK's load_memory pattern.
        
        Args:
            query: Search query
            user_id: User identifier (defaults to "default_user")
            max_results: Maximum results to return
            
        Returns:
            Formatted memory results for agent consumption
        """
        try:
            # Use the underlying memory tool
            result = await self.memory_tool(
                user_id=user_id,
                query=query,
                max_results=max_results
            )
            
            if result["success"] and result["results"]:
                # Format results for agent consumption
                formatted_results = []
                for memory_result in result["results"]:
                    formatted_results.append({
                        "content": memory_result.get("content", ""),
                        "session": memory_result.get("session_id", ""),
                        "timestamp": memory_result.get("timestamp", ""),
                        "relevance": memory_result.get("score", 0.0)
                    })
                
                return {
                    "success": True,
                    "memory_results": formatted_results,
                    "total_found": result["total_found"],
                    "summary": f"Found {len(formatted_results)} relevant memories for '{query}'"
                }
            else:
                return {
                    "success": True,
                    "memory_results": [],
                    "total_found": 0,
                    "summary": f"No relevant memories found for '{query}'"
                }
                
        except Exception as e:
            logger.error(f"LoadMemoryTool failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_results": [],
                "total_found": 0
            }