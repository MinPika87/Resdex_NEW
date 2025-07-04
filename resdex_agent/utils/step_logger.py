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
    def log_facet_generation(self, query: str, categories_count: int = 0):
        """Log facet generation request."""
        if categories_count > 0:
            self.log_step(f"🔍 Generated {categories_count} facet categories for: '{query[:50]}...'", "facets")
        else:
            self.log_step(f"🔍 Generating facets for: '{query[:50]}...'", "facets")

    def log_query_relaxation(self, suggestions_count: int = 0):
        """Log query relaxation suggestions."""
        if suggestions_count > 0:
            self.log_step(f"🔄 Generated {suggestions_count} query relaxation suggestions", "relaxation")
        else:
            self.log_step(f"🔄 Analyzing query for relaxation opportunities", "relaxation")

    def log_refinement_api_call(self, api_url: str, status: str = "calling"):
        """Log refinement API calls."""
        if status == "calling":
            self.log_step(f"📡 Calling facet generation API", "api")
        elif status == "success":
            self.log_step(f"✅ Facet API call successful", "api")
        elif status == "failed":
            self.log_step(f"❌ Facet API call failed", "api")

    def log_refinement_routing(self, refinement_type: str):
        """Log refinement agent routing decisions."""
        type_mapping = {
            "facet_generation": "🔍 Facet Generation",
            "query_relaxation": "🔄 Query Relaxation",
            "auto_refinement": "🤖 Auto Refinement"
        }
        
        display_type = type_mapping.get(refinement_type, refinement_type)
        self.log_step(f"🎯 Refinement routing: {display_type}", "routing")

    def log_facet_processing(self, result_1_count: int, result_2_count: int):
        """Log facet processing results."""
        total_categories = result_1_count + result_2_count
        self.log_step(f"🔧 Processed facets: {result_1_count} primary + {result_2_count} secondary = {total_categories} total", "processing")

    def log_refinement_completion(self, refinement_type: str, success: bool = True):
        """Log completion of refinement processing."""
        if success:
            type_mapping = {
                "facet_generation": "Facet generation completed",
                "query_relaxation": "Query relaxation completed",
                "auto_refinement": "Auto refinement completed"
            }
            
            message = type_mapping.get(refinement_type, f"{refinement_type} completed")
            self.log_step(f"🎯 {message}", "completion")
        else:
            self.log_step(f"❌ Refinement failed: {refinement_type}", "error")

    def log_auto_trigger(self, trigger_type: str, condition: str):
        """Log auto-trigger events for refinement."""
        trigger_mapping = {
            "facet_auto": "🤖 Auto-triggering facet generation",
            "relaxation_auto": "🤖 Auto-triggering query relaxation",
            "refinement_suggested": "💡 Refinement suggested"
        }
        
        display_message = trigger_mapping.get(trigger_type, f"Auto-trigger: {trigger_type}")
        self.log_step(f"{display_message}: {condition}", "auto_trigger")
    def log_query_relaxation(self, suggestions_count: int = 0, current_count: int = 0, estimated_increase: int = 0):
        """Log query relaxation suggestions."""
        if suggestions_count > 0:
            if estimated_increase > 0:
                self.log_step(f"🔄 Generated {suggestions_count} relaxation suggestions (+{estimated_increase:,} potential candidates)", "relaxation")
            else:
                self.log_step(f"🔄 Generated {suggestions_count} query relaxation suggestions", "relaxation")
        else:
            self.log_step(f"🔄 Analyzing query for relaxation opportunities", "relaxation")

    def log_relaxation_api_call(self, api_url: str, current_count: int, status: str = "calling"):
        """Log query relaxation API calls."""
        if status == "calling":
            self.log_step(f"📡 Calling query relaxation API (current: {current_count} candidates)", "api")
        elif status == "success":
            self.log_step(f"✅ Query relaxation API call successful", "api")
        elif status == "failed":
            self.log_step(f"❌ Query relaxation API call failed", "api")

    def log_relaxation_strategy(self, strategy_type: str, description: str = ""):
        """Log relaxation strategy application."""
        strategy_mapping = {
            "skill_relaxation": "🔧 Skill Relaxation",
            "experience_relaxation": "📈 Experience Range Relaxation", 
            "location_relaxation": "🌍 Location Relaxation",
            "salary_relaxation": "💰 Salary Range Relaxation",
            "remote_work": "🏠 Remote Work Option",
            "fallback_suggestions": "🛠️ Fallback Suggestions"
        }
        
        display_type = strategy_mapping.get(strategy_type, strategy_type)
        message = f"{display_type}: {description}" if description else display_type
        self.log_step(message, "strategy")

    def log_relaxation_conversion(self, session_filters: Dict[str, Any], api_format: str = "converted"):
        """Log session state to API conversion for relaxation."""
        skills_count = len(session_filters.get('keywords', []))
        exp_range = f"{session_filters.get('min_exp', 0)}-{session_filters.get('max_exp', 10)}"
        cities_count = len(session_filters.get('current_cities', [])) + len(session_filters.get('preferred_cities', []))
        
        self.log_step(f"🔧 Converting filters to API format: {skills_count} skills, {exp_range}y exp, {cities_count} cities", "conversion")

    def log_relaxation_parsing(self, suggestions_count: int, method: str = "api"):
        """Log relaxation response parsing."""
        method_text = {
            "api": "API response",
            "fallback": "fallback rules",
            "rule_based": "rule-based analysis"
        }.get(method, method)
        
        self.log_step(f"🔧 Parsed {suggestions_count} suggestions from {method_text}", "parsing")

    def log_refinement_routing(self, refinement_type: str):
        """ENHANCED: Log refinement agent routing decisions."""
        type_mapping = {
            "facet_generation": "🔍 Facet Generation",
            "query_relaxation": "🔄 Query Relaxation",  # NEW
            "auto_refinement": "🤖 Auto Refinement"
        }
        
        display_type = type_mapping.get(refinement_type, refinement_type)
        self.log_step(f"🎯 Refinement routing: {display_type}", "routing")

    def log_refinement_completion(self, refinement_type: str, success: bool = True, result_summary: str = ""):
        """ENHANCED: Log completion of refinement processing."""
        if success:
            type_mapping = {
                "facet_generation": "Facet generation completed",
                "query_relaxation": "Query relaxation completed",  # NEW
                "auto_refinement": "Auto refinement completed"
            }
            
            message = type_mapping.get(refinement_type, f"{refinement_type} completed")
            if result_summary:
                message += f": {result_summary}"
            self.log_step(f"🎯 {message}", "completion")
        else:
            self.log_step(f"❌ Refinement failed: {refinement_type}", "error")

    def log_relaxation_impact_estimate(self, current_count: int, estimated_increase: int, confidence: float = 0.0):
        """Log estimated impact of relaxation suggestions."""
        if estimated_increase > 0:
            percentage_increase = int((estimated_increase / max(current_count, 1)) * 100)
            confidence_text = f" (confidence: {confidence:.1f})" if confidence > 0 else ""
            self.log_step(f"📊 Impact estimate: +{estimated_increase:,} candidates ({percentage_increase}% increase){confidence_text}", "impact")
        else:
            self.log_step(f"📊 Estimating relaxation impact for {current_count} current candidates", "impact")

    def log_auto_trigger(self, trigger_type: str, condition: str):
        """ENHANCED: Log auto-trigger events for refinement."""
        trigger_mapping = {
            "facet_auto": "🤖 Auto-triggering facet generation",
            "relaxation_auto": "🤖 Auto-triggering query relaxation",  # NEW
            "refinement_suggested": "💡 Refinement suggested"
        }
        
        display_message = trigger_mapping.get(trigger_type, f"Auto-trigger: {trigger_type}")
        self.log_step(f"{display_message}: {condition}", "auto_trigger")
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