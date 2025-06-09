"""
Real-time step logging system for ResDex Agent UI.
"""
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading


class StepLogger:
    """
    Session-state managed step logger for real-time UI updates.
    Singleton pattern to ensure consistent logging across all components.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StepLogger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.steps: List[Dict[str, Any]] = []
            self.current_session_id: Optional[str] = None
            self._initialized = True
    
    def start_session(self, session_id: str):
        """Start a new logging session."""
        self.current_session_id = session_id
        self.steps = []
        self.log_step("✅ Root Agent Initialized", "system")
    
    def log_step(self, message: str, step_type: str = "info", details: Optional[str] = None):
        """Log a new step with timestamp."""
        if not self.current_session_id:
            return
            
        step = {
            "id": len(self.steps),
            "message": message,
            "type": step_type,
            "details": details,
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "session_id": self.current_session_id
        }
        self.steps.append(step)
        print(f"🔍 STEP LOGGED: {message}")  # For backend debugging
    
    def get_steps(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all steps for current or specified session."""
        if session_id:
            return [step for step in self.steps if step["session_id"] == session_id]
        return self.steps.copy()
    
    def clear_steps(self):
        """Clear all steps for current session."""
        self.steps = []
    
    def log_routing_decision(self, user_input: str, decision: str, confidence: float = 0.0):
        """Log routing decision with classification details."""
        self.log_step(f"🔍 Classifying user input: \"{user_input[:50]}{'...' if len(user_input) > 50 else ''}\"", "routing")
        self.log_step(f"➡️ Routing decision: {decision} (confidence: {confidence:.2f})", "decision")
    
    def log_tool_activation(self, tool_name: str, action: str = ""):
        """Log tool activation."""
        action_text = f" - {action}" if action else ""
        self.log_step(f"🔧 {tool_name} activated{action_text}", "tool")
    
    def log_llm_call(self, model: str, task: str):
        """Log LLM API call."""
        self.log_step(f"🤖 LLM Call: {model} for {task}", "llm")
    
    def log_search_execution(self, filters: Dict[str, Any]):
        """Log search execution with filter summary."""
        filter_summary = []
        if filters.get('keywords'):
            filter_summary.append(f"{len(filters['keywords'])} skills")
        if filters.get('current_cities') or filters.get('preferred_cities'):
            total_cities = len(filters.get('current_cities', [])) + len(filters.get('preferred_cities', []))
            filter_summary.append(f"{total_cities} locations")
        if filters.get('min_exp', 0) > 0 or filters.get('max_exp', 50) < 50:
            filter_summary.append(f"exp: {filters.get('min_exp', 0)}-{filters.get('max_exp', 10)}y")
        
        summary = ", ".join(filter_summary) if filter_summary else "basic criteria"
        self.log_step(f"📊 Executing search with {summary}", "search")
    
    def log_results(self, count: int, total: int):
        """Log search results."""
        self.log_step(f"✅ Found {count} candidates from {total:,} total matches", "results")
    
    def log_completion(self, message: str = "Processing complete"):
        """Log completion of processing."""
        self.log_step(f"🎯 {message}", "completion")
    
    def log_error(self, error: str):
        """Log error occurrence."""
        self.log_step(f"❌ Error: {error}", "error")


# Global instance
step_logger = StepLogger()