# resdex_agent/sub_agents/general_query/config.py
"""
Configuration for General Query Sub-Agent.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class GeneralQueryConfig(BaseModel):
    """Configuration for General Query Sub-Agent."""
    
    # Basic agent info
    name: str = "GeneralQueryAgent"
    version: str = "1.0.0"
    description: str = "Handle conversational queries and explanations using LLM streaming"
    
    # LLM settings for conversational responses
    conversation_temperature: float = 0.7
    conversation_max_tokens: int = 1500
    
    # Response settings
    max_response_length: int = 1000
    include_suggestions: bool = True
    
    # Conversation types
    supported_queries: Dict[str, bool] = Field(default_factory=lambda: {
        "greetings": True,
        "help_requests": True,
        "explanations": True,
        "system_info": True,
        "capability_questions": True
    })