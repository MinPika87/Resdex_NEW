# resdex_agent/utils/step_logger.py - ENHANCED for live streaming
"""
Real-time step logging system for ResDex Agent UI with enhanced live streaming support.
"""
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading


class StepLogger:
    """
    Enhanced session-state managed step logger for real-time UI updates.
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
            self.sessions: Dict[str, List[Dict[str, Any]]] = {}
            self.current_session_id: Optional[str] = None
            self._initialized = True
    
    def start_session(self, session_id: str):
        """Start a new logging session."""
        self.current_session_id = session_id
        self.sessions[session_id] = []
        self.log_step("✅ Root Agent Initialized", "system")
    
    def log_step(self, message: str, step_type: str = "info", details: Optional[str] = None):
        """Log a new step with timestamp."""
        if not self.current_session_id:
            return
            
        session_steps = self.sessions.get(self.current_session_id, [])
        
        step = {
            "id": len(session_steps),
            "message": message,
            "type": step_type,
            "details": details,
            "timestamp": datetime.now().strftime("%H:%M:%S"),  # Simple HH:MM:SS format
            "session_id": self.current_session_id,
            "created_at": time.time()  # For ordering and performance tracking
        }
        
        session_steps.append(step)
        self.sessions[self.current_session_id] = session_steps
        
        print(f"🔍 STEP LOGGED: {message}")  # For backend debugging
    
    def get_steps(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all steps for current or specified session."""
        target_session = session_id or self.current_session_id
        if target_session and target_session in self.sessions:
            return self.sessions[target_session].copy()
        return []
    
    def get_latest_step(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the latest step for a session."""
        steps = self.get_steps(session_id)
        return steps[-1] if steps else None
    
    def get_step_count(self, session_id: Optional[str] = None) -> int:
        """Get the number of steps for a session."""
        return len(self.get_steps(session_id))
    
    def is_session_complete(self, session_id: Optional[str] = None) -> bool:
        """Check if a session is complete (ended with completion or error)."""
        latest_step = self.get_latest_step(session_id)
        if latest_step:
            return latest_step["type"] in ["completion", "error"]
        return False
    
    def clear_steps(self, session_id: Optional[str] = None):
        """Clear all steps for current or specified session."""
        target_session = session_id or self.current_session_id
        if target_session and target_session in self.sessions:
            self.sessions[target_session] = []
    
    def clear_old_sessions(self, max_age_minutes: int = 30):
        """Clear sessions older than max_age_minutes."""
        current_time = time.time()
        cutoff_time = current_time - (max_age_minutes * 60)
        
        sessions_to_remove = []
        for session_id, steps in self.sessions.items():
            if steps and steps[-1].get("created_at", 0) < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
    
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
    
    def log_processing_time(self, operation: str, start_time: float):
        """Log processing time for an operation."""
        duration = time.time() - start_time
        self.log_step(f"⏱️ {operation} completed in {duration:.2f}s", "info")
    
    def get_session_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of a session's processing."""
        steps = self.get_steps(session_id)
        if not steps:
            return {"total_steps": 0, "status": "empty", "duration": 0}
        
        first_step = steps[0]
        last_step = steps[-1]
        
        duration = 0
        if "created_at" in first_step and "created_at" in last_step:
            duration = last_step["created_at"] - first_step["created_at"]
        
        step_types = {}
        for step in steps:
            step_type = step["type"]
            step_types[step_type] = step_types.get(step_type, 0) + 1
        
        status = "in_progress"
        if last_step["type"] == "completion":
            status = "completed"
        elif last_step["type"] == "error":
            status = "error"
        
        return {
            "total_steps": len(steps),
            "status": status,
            "duration": duration,
            "step_types": step_types,
            "start_time": first_step.get("timestamp", ""),
            "end_time": last_step.get("timestamp", ""),
            "last_message": last_step.get("message", "")
        }
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all active sessions."""
        summaries = {}
        for session_id in self.sessions.keys():
            summaries[session_id] = self.get_session_summary(session_id)
        return summaries
    
    def export_session_log(self, session_id: Optional[str] = None) -> str:
        """Export session steps as formatted text log."""
        steps = self.get_steps(session_id)
        if not steps:
            return "No steps found for session."
        
        target_session = session_id or self.current_session_id
        log_lines = [
            f"=== ResDex Agent Session Log ===",
            f"Session ID: {target_session}",
            f"Total Steps: {len(steps)}",
            f"Status: {self.get_session_summary(session_id)['status']}",
            "=" * 40,
            ""
        ]
        
        for step in steps:
            timestamp = step.get("timestamp", "")
            step_type = step.get("type", "info").upper()
            message = step.get("message", "")
            
            log_lines.append(f"[{timestamp}] {step_type}: {message}")
            
            if step.get("details"):
                log_lines.append(f"    Details: {step['details']}")
        
        log_lines.append("")
        log_lines.append("=== End of Log ===")
        
        return "\n".join(log_lines)


# Global instance
step_logger = StepLogger()