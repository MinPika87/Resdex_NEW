# resdex_agent/ui/components/step_display.py - FIXED for Streamlit threading
"""
Real-time step display component - Fixed for Streamlit 1.12 threading limitations
"""

import streamlit as st
import time
from typing import Dict, Any, List, Optional
from ...utils.step_logger import step_logger


class StepDisplay:
    """Component for displaying real-time processing steps - Fixed for Streamlit threading."""
    
    def __init__(self):
        self.step_icons = {
            "system": "⚙️",
            "routing": "🔍", 
            "decision": "➡️",
            "tool": "🔧",
            "llm": "🤖",
            "search": "📊",
            "results": "✅",
            "completion": "🎯",
            "error": "❌",
            "info": "💡"
        }
        
        self.step_colors = {
            "system": "#6c757d",
            "routing": "#17a2b8",
            "decision": "#28a745", 
            "tool": "#fd7e14",
            "llm": "#6f42c1",
            "search": "#20c997",
            "results": "#28a745",
            "completion": "#007bff",
            "error": "#dc3545",
            "info": "#6c757d"
        }
    
    def create_step_placeholder(self) -> Any:
        """Create a placeholder for step updates."""
        return st.empty()
    
    def show_processing_steps(self, session_id: str, placeholder, max_wait: int = 20):
        """
        FIXED: Show steps using session state polling instead of threading.
        This method should be called from the main Streamlit thread.
        """
        try:
            # Poll for steps from session state rather than using threads
            if 'step_poll_count' not in st.session_state:
                st.session_state.step_poll_count = 0
            
            # Get current steps
            current_steps = step_logger.get_steps(session_id)
            
            if current_steps:
                # Update display with current steps
                self._safe_update_step_display(placeholder, current_steps)
                
                # Check if processing is complete
                if current_steps and current_steps[-1]["type"] in ["completion", "error"]:
                    # Mark as complete
                    st.session_state[f'steps_complete_{session_id}'] = True
                    # Schedule cleanup after small delay
                    st.session_state[f'steps_cleanup_time_{session_id}'] = time.time() + 2
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Step display error: {e}")
            return False
    
    def _safe_update_step_display(self, placeholder, steps: List[Dict[str, Any]]):
        """FIXED: Safely update step display without threading issues."""
        if not steps:
            return
        
        try:
            # Build simple HTML for steps (avoid complex animations in threading)
            steps_html = """
            <div style="
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
                margin: 8px 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            ">
                <div style="
                    font-weight: 600;
                    color: #495057;
                    margin-bottom: 8px;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                ">🔄 AI Processing Steps</div>
            """
            
            # Show only last 5 steps to avoid overwhelming UI
            recent_steps = steps[-5:] if len(steps) > 5 else steps
            
            for step in recent_steps:
                icon = self.step_icons.get(step["type"], "💡")
                color = self.step_colors.get(step["type"], "#6c757d")
                
                step_html = f"""
                <div style="
                    display: flex;
                    align-items: center;
                    margin: 4px 0;
                    padding: 6px 10px;
                    background: white;
                    border-radius: 4px;
                    border-left: 3px solid {color};
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                ">
                    <span style="font-size: 14px; margin-right: 8px;">{icon}</span>
                    <span style="color: #343a40; font-size: 12px; flex-grow: 1;">{step['message']}</span>
                    <span style="color: #6c757d; font-size: 10px; margin-left: 8px;">{step['timestamp']}</span>
                </div>
                """
                steps_html += step_html
            
            steps_html += "</div>"
            
            # FIXED: Use markdown instead of direct DOM manipulation
            placeholder.markdown(steps_html, unsafe_allow_html=True)
            
        except Exception as e:
            print(f"❌ Error updating step display: {e}")
            # Fallback to simple text display
            try:
                simple_text = f"🔄 Processing... ({len(steps)} steps completed)"
                placeholder.text(simple_text)
            except:
                pass  # Silent fail if even simple text fails
    
    def cleanup_completed_steps(self, session_id: str, placeholder):
        """Clean up completed step displays."""
        try:
            cleanup_time_key = f'steps_cleanup_time_{session_id}'
            complete_key = f'steps_complete_{session_id}'
            
            if (complete_key in st.session_state and 
                cleanup_time_key in st.session_state and 
                time.time() >= st.session_state[cleanup_time_key]):
                
                # Clear the display
                placeholder.empty()
                
                # Clean up session state
                if complete_key in st.session_state:
                    del st.session_state[complete_key]
                if cleanup_time_key in st.session_state:
                    del st.session_state[cleanup_time_key]
                    
                return True
            return False
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
            return False
    
    def clear_display(self, placeholder_key: str = "step_display"):
        """Clear the step display."""
        try:
            if f"{placeholder_key}_container" in st.session_state:
                st.session_state[f"{placeholder_key}_container"].empty()
                del st.session_state[f"{placeholder_key}_container"]
        except Exception as e:
            print(f"❌ Clear display error: {e}")
    
    def render_static_steps(self, steps: List[Dict[str, Any]]):
        """Render steps in a static container (for completed processes)."""
        if not steps:
            return
        
        try:
            with st.container():
                st.markdown("### 🔄 Processing Steps")
                
                for step in steps:
                    icon = self.step_icons.get(step["type"], "💡")
                    col1, col2, col3 = st.columns([1, 10, 2])
                    with col1:
                        st.markdown(f"<span style='font-size: 16px;'>{icon}</span>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"<span style='color: #495057; font-weight: 500;'>{step['message']}</span>", unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"<small style='color: #6c757d;'>{step['timestamp']}</small>", unsafe_allow_html=True)
        except Exception as e:
            print(f"❌ Static steps render error: {e}")


# FIXED: Simplified step display functions for immediate use
def show_simple_steps(session_id: str, placeholder):
    """Show steps using simple polling approach."""
    try:
        steps = step_logger.get_steps(session_id)
        if steps:
            # Simple text display
            step_text = f"🔄 **AI Processing:** {steps[-1]['message']}"
            placeholder.markdown(step_text)
            
            # Check if complete
            if steps[-1]["type"] in ["completion", "error"]:
                # Clear after delay
                time.sleep(1)
                placeholder.empty()
                return True
        return False
    except Exception as e:
        print(f"❌ Simple steps error: {e}")
        return False