# resdex_agent/ui/components/step_display.py - FIXED for LIVE step streaming
"""
Real-time step display component - Fixed for live streaming in Streamlit 1.12
"""

import streamlit as st
import time
from typing import Dict, Any, List, Optional
from ...utils.step_logger import step_logger


class StepDisplay:
    """Component for displaying LIVE streaming steps - Fixed for Streamlit 1.12"""
    
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
    
    def show_live_steps(self, session_id: str, placeholder, max_steps: int = 10):
        """
        FIXED: Show ALL steps as they happen - LIVE STREAMING
        """
        try:
            current_steps = step_logger.get_steps(session_id)
            
            if current_steps:
                # Show ALL steps (not just latest) with live updates
                self._render_live_steps_container(placeholder, current_steps, max_steps)
                
                # Check if processing is complete
                if current_steps and current_steps[-1]["type"] in ["completion", "error"]:
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Live step display error: {e}")
            return False
    
    def _render_live_steps_container(self, placeholder, steps: List[Dict[str, Any]], max_steps: int = 10):
        """FIXED: Avoid nested columns error - use simple HTML structure"""
        if not steps:
            return
        
        try:
            # Show recent steps (last N steps to avoid overwhelming UI)
            display_steps = steps[-max_steps:] if len(steps) > max_steps else steps
            
            # Build HTML without nested columns
            steps_html = """
            <div style="
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
                margin: 8px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-height: 400px;
                overflow-y: auto;
            ">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-weight: 600;
                    color: #495057;
                    margin-bottom: 10px;
                    font-size: 14px;
                ">
                    <span>🔄 AI Processing Steps</span>
                    <span style="
                        font-size: 10px;
                        background: #28a745;
                        color: white;
                        padding: 2px 6px;
                        border-radius: 8px;
                        font-weight: bold;
                    ">LIVE</span>
                </div>
            """
            
            # Add ALL accumulated steps
            for i, step in enumerate(display_steps):
                icon = self.step_icons.get(step["type"], "💡")
                color = self.step_colors.get(step["type"], "#6c757d")
                
                # Different styling for latest step vs previous steps
                is_latest = (i == len(display_steps) - 1)
                
                if is_latest:
                    # Latest step - highlighted
                    steps_html += f"""
                    <div style="
                        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
                        border-left: 4px solid {color};
                        padding: 8px 12px;
                        margin: 4px 0;
                        border-radius: 4px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                    ">
                        <div style="display: flex; align-items: center;">
                            <span style="font-size: 14px; margin-right: 8px;">{icon}</span>
                            <strong>{step['message']}</strong>
                        </div>
                        <span style="font-size: 10px; color: #666; font-family: monospace;">{step['timestamp']}</span>
                    </div>
                    """
                else:
                    # Previous steps - muted but visible
                    steps_html += f"""
                    <div style="
                        background: #f8f9fa;
                        border-left: 3px solid {color};
                        padding: 6px 10px;
                        margin: 2px 0;
                        border-radius: 3px;
                        opacity: 0.8;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                    ">
                        <div style="display: flex; align-items: center;">
                            <span style="font-size: 12px; margin-right: 6px;">{icon}</span>
                            <span style="color: #666;">{step['message']}</span>
                        </div>
                        <span style="font-size: 9px; color: #999; font-family: monospace;">{step['timestamp']}</span>
                    </div>
                    """
            
            # Progress summary
            if len(steps) > max_steps:
                steps_html += f"""
                <div style="
                    text-align: center;
                    margin-top: 8px;
                    font-size: 11px;
                    color: #6c757d;
                    font-style: italic;
                ">
                    📊 Showing latest {max_steps} of {len(steps)} total steps
                </div>
                """
            else:
                steps_html += f"""
                <div style="
                    text-align: center;
                    margin-top: 8px;
                    font-size: 11px;
                    color: #6c757d;
                    font-style: italic;
                ">
                    📊 {len(steps)} processing steps
                </div>
                """
            
            steps_html += "</div>"
            
            # Update placeholder with ALL steps using HTML
            placeholder.markdown(steps_html, unsafe_allow_html=True)
            
        except Exception as e:
            print(f"❌ Error rendering live steps: {e}")
            # Simple fallback
            try:
                if steps:
                    latest_step = steps[-1]
                    placeholder.markdown(f"🔄 **Step {len(steps)}:** {latest_step['message']}")
            except:
                placeholder.markdown("🔄 **Processing...**")


# FIXED: Simplified step polling for real-time updates
def poll_and_update_steps(session_id: str, placeholder, max_polls: int = 50):
    """
    FIXED: Poll for steps and update display - works with Streamlit 1.12
    """
    step_display = StepDisplay()
    
    for poll_count in range(max_polls):
        try:
            # Get current steps
            current_steps = step_logger.get_steps(session_id)
            
            if current_steps:
                # Update display with ALL steps
                step_display._render_live_steps_container(placeholder, current_steps)
                
                # Check if complete
                if current_steps[-1]["type"] in ["completion", "error"]:
                    # Keep final display for a moment
                    time.sleep(2)
                    return True
            
            # Small delay between polls
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Step polling error: {e}")
            break
    
    return False