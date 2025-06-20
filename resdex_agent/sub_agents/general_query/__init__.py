# resdex_agent/sub_agents/general_query/__init__.py
"""
General Query Sub-Agent for conversational responses.
"""

from .agent import GeneralQueryAgent
from .config import GeneralQueryConfig

__all__ = [
    "GeneralQueryAgent",
    "GeneralQueryConfig"
]
