"""
ResDex Agent - AI-powered candidate search and filtering system.

This package provides a modular agent framework for processing natural language
search requests and managing candidate search filters following Google ADK patterns.
"""

from .agent import ResDexRootAgent
from .config import AgentConfig

__version__ = "1.0.0"
__author__ = "ResDex Team"

__all__ = [
    "ResDexRootAgent",
    "AgentConfig",
    "agent"
]