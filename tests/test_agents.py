"""
Unit tests for ResDex Agent components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from google.adk.core.content import Content

from resdex_agent.agent import ResDexRootAgent
from resdex_agent.sub_agents.search_interaction.agent import SearchInteractionAgent
from resdx_agent.config import AgentConfig


class TestResDexRootAgent:
    """Test cases for the root agent."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        config = AgentConfig()
        return ResDexRootAgent(config)
    
    @pytest.mark.asyncio
    async def test_health_check(self, agent):
        """Test agent health check functionality."""
        content = Content(data={"request_type": "health_check"})
        result = await agent.execute(content)
        
        assert result.data["success"] == True
        assert result.data["status"] == "healthy"
        assert "root_agent" in result.data
        assert "sub_agents" in result.data
    
    @pytest.mark.asyncio
    async def test_search_interaction_delegation(self, agent):
        """Test delegation to search interaction sub-agent."""
        content = Content(data={
            "request_type": "search_interaction",
            "user_input": "add python skill",
            "session_state": {"keywords": []}
        })
        
        with patch.object(agent.sub_agents["search_interaction"], 'execute') as mock_execute:
            mock_execute.return_value = Content(data={"success": True, "message": "Skill added"})
            
            result = await agent.execute(content)
            
            assert result.data["success"] == True
            assert "root_agent" in result.data
            mock_execute.assert_called_once()


class TestSearchInteractionAgent:
    """Test cases for the search interaction sub-agent."""
    
    @pytest.fixture
    def agent(self):
        """Create a test search interaction agent."""
        return SearchInteractionAgent()
    
    @pytest.mark.asyncio
    async def test_skill_addition(self, agent):
        """Test adding a skill through natural language."""
        content = Content(data={
            "user_input": "add python as mandatory",
            "session_state": {"keywords": []}
        })
        
        with patch.object(agent.tools["llm_tool"], '__call__') as mock_llm:
            mock_llm.return_value = {
                "success": True,
                "intent_data": {
                    "action": "add_skill",
                    "value": "Python",
                    "mandatory": True,
                    "response_text": "Added Python as mandatory skill",
                    "trigger_search": False
                }
            }
            
            result = await agent.execute(content)
            
            assert result.data["success"] == True
            assert "Python" in str(result.data["session_state"]["keywords"])
            assert result.data["trigger_search"] == False
