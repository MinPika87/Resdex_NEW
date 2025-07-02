# resdex_agent/ui/components/relaxation_display.py
"""
UI Component for displaying query relaxation suggestions.
"""

import streamlit as st
from typing import Dict, Any, List, Optional


class RelaxationDisplay:
    """UI component for displaying query relaxation suggestions and results."""
    
    def __init__(self, session_state: Dict[str, Any], root_agent=None):
        self.session_state = session_state
        self.root_agent = root_agent
        
        # Styling for relaxation suggestions
        self.suggestion_styles = {
            "skill_relaxation": {"color": "#FF6B6B", "icon": "🔧"},
            "experience_relaxation": {"color": "#4ECDC4", "icon": "📈"},
            "location_relaxation": {"color": "#45B7D1", "icon": "🌍"},
            "salary_relaxation": {"color": "#96CEB4", "icon": "💰"},
            "remote_work": {"color": "#FFEAA7", "icon": "🏠"},
            "general": {"color": "#DDA0DD", "icon": "💡"}
        }
    
    def render_relaxation_results(self, relaxation_data: Dict[str, Any]):
        """Render query relaxation results in the main interface."""
        try:
            if not relaxation_data or not relaxation_data.get("success", False):
                st.warning("Query relaxation suggestions are not available at this time.")
                return
            
            suggestions = relaxation_data.get("relaxation_suggestions", [])
            current_count = relaxation_data.get("current_count", 0)
            estimated_increase = relaxation_data.get("estimated_new_count", 0)
            
            if not suggestions:
                st.info("No specific relaxation suggestions available for your current search.")
                return
            
            # Header with impact summary
            st.markdown("### 🔄 Query Relaxation Suggestions")
            
            if estimated_increase > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Results", f"{current_count:,}")
                with col2:
                    st.metric("Potential Increase", f"+{estimated_increase:,}")
                with col3:
                    improvement_pct = int((estimated_increase / max(current_count, 1)) * 100)
                    st.metric("Improvement", f"{improvement_pct}%")
            
            st.markdown("---")
            
            # Display suggestions
            self._render_suggestion_cards(suggestions)
            
            # Action buttons
            self._render_relaxation_actions(suggestions, relaxation_data)
            
        except Exception as e:
            st.error(f"Error displaying relaxation results: {e}")
    
    def _render_suggestion_cards(self, suggestions: List[Dict[str, Any]]):
        """Render individual suggestion cards."""
        st.markdown("#### 💡 Recommended Actions")
        
        # Display suggestions in rows of 2
        for i in range(0, len(suggestions), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(suggestions):
                    suggestion = suggestions[i + j]
                    self._render_single_suggestion_card(col, suggestion, i + j + 1)
    
    def _render_single_suggestion_card(self, container, suggestion: Dict[str, Any], index: int):
        """Render a single suggestion card."""
        try:
            suggestion_type = suggestion.get('type', 'general')
            title = suggestion.get('title', f'Suggestion {index}')
            description = suggestion.get('description', 'No description available')
            impact = suggestion.get('impact', 'Impact unknown')
            action = suggestion.get('action', 'No action specified')
            confidence = suggestion.get('confidence', 0.5)
            
            # Get styling
            style = self.suggestion_styles.get(suggestion_type, self.suggestion_styles['general'])
            color = style['color']
            icon = style['icon']
            
            with container:
                # Create card with custom styling
                st.markdown(f"""
                <div style="
                    border: 2px solid {color};
                    border-radius: 10px;
                    padding: 15px;
                    margin: 10px 0;
                    background: linear-gradient(135deg, {color}15, {color}05);
                    height: 200px;
                    display: flex;
                    flex-direction: column;
                ">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <span style="font-size: 24px; margin-right: 10px;">{icon}</span>
                        <h4 style="margin: 0; color: {color}; font-size: 16px;">{title}</h4>
                    </div>
                    
                    <p style="
                        color: #333; 
                        font-size: 13px; 
                        flex-grow: 1; 
                        margin: 8px 0;
                        line-height: 1.4;
                    ">{description}</p>
                    
                    <div style="margin: 8px 0;">
                        <strong style="color: {color}; font-size: 12px;">Expected Impact:</strong>
                        <br><span style="font-size: 11px; color: #666;">{impact}</span>
                    </div>
                    
                    <div style="margin-top: auto;">
                        <div style="
                            background: {color}20; 
                            padding: 6px 8px; 
                            border-radius: 5px; 
                            font-size: 11px; 
                            color: #555;
                            border-left: 3px solid {color};
                        ">
                            <strong>Action:</strong> {action}
                        </div>
                    </div>
                    
                    <div style="text-align: right; margin-top: 8px;">
                        <span style="
                            background: {color}30; 
                            color: {color}; 
                            padding: 2px 6px; 
                            border-radius: 10px; 
                            font-size: 10px; 
                            font-weight: bold;
                        ">
                            Confidence: {confidence:.0%}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            container.error(f"Error rendering suggestion: {e}")
    
    def _render_relaxation_actions(self, suggestions: List[Dict[str, Any]], relaxation_data: Dict[str, Any]):
        """Render action buttons for relaxation suggestions."""
        st.markdown("---")
        st.markdown("#### 🎯 Take Action")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Apply Top Suggestion", key="apply_top_relaxation"):
                if suggestions:
                    self._apply_relaxation_suggestion(suggestions[0])
        
        with col2:
            if st.button("🔧 Apply All Suggestions", key="apply_all_relaxation"):
                self._apply_multiple_suggestions(suggestions)
        
        with col3:
            if st.button("💾 Save Suggestions", key="save_relaxation"):
                self._save_relaxation_suggestions(suggestions, relaxation_data)
        
        # Advanced options
        with st.expander("🛠️ Advanced Relaxation Options"):
            self._render_advanced_relaxation_options(suggestions, relaxation_data)
    
    def _render_advanced_relaxation_options(self, suggestions: List[Dict[str, Any]], relaxation_data: Dict[str, Any]):
        """Render advanced relaxation options."""
        st.markdown("**Choose specific suggestions to apply:**")
        
        selected_suggestions = []
        for i, suggestion in enumerate(suggestions):
            title = suggestion.get('title', f'Suggestion {i+1}')
            impact = suggestion.get('impact', 'Unknown impact')
            
            if st.checkbox(f"{title} - {impact}", key=f"suggestion_{i}"):
                selected_suggestions.append(suggestion)
        
        if selected_suggestions:
            if st.button("Apply Selected Suggestions", key="apply_selected"):
                self._apply_multiple_suggestions(selected_suggestions)
        
        # Manual relaxation controls
        st.markdown("---")
        st.markdown("**Manual Relaxation Controls:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔧 Reduce Required Skills", key="manual_skill_relax"):
                self._manual_skill_relaxation()
            
            if st.button("📈 Expand Experience Range", key="manual_exp_relax"):
                self._manual_experience_relaxation()
        
        with col2:
            if st.button("🌍 Add More Locations", key="manual_loc_relax"):
                self._manual_location_relaxation()
            
            if st.button("💰 Increase Salary Range", key="manual_salary_relax"):
                self._manual_salary_relaxation()
    
    def _apply_relaxation_suggestion(self, suggestion: Dict[str, Any]):
        """Apply a single relaxation suggestion."""
        try:
            suggestion_type = suggestion.get('type', 'general')
            
            if suggestion_type == 'skill_relaxation':
                self._apply_skill_relaxation(suggestion)
            elif suggestion_type == 'experience_relaxation':
                self._apply_experience_relaxation(suggestion)
            elif suggestion_type == 'location_relaxation':
                self._apply_location_relaxation(suggestion)
            elif suggestion_type == 'salary_relaxation':
                self._apply_salary_relaxation(suggestion)
            else:
                st.info(f"Applied suggestion: {suggestion.get('title', 'Unknown')}")
            
            st.success(f"✅ Applied: {suggestion.get('title', 'Relaxation suggestion')}")
            st.experimental_rerun()
            
        except Exception as e:
            st.error(f"Failed to apply suggestion: {e}")
    
    def _apply_skill_relaxation(self, suggestion: Dict[str, Any]):
        """Apply skill relaxation suggestion."""
        current_keywords = self.session_state.get('keywords', [])
        if len(current_keywords) > 3:
            # Remove 2-3 skills
            skills_to_remove = min(3, len(current_keywords) - 2)
            new_keywords = current_keywords[:-skills_to_remove]
            self.session_state['keywords'] = new_keywords
    
    def _apply_experience_relaxation(self, suggestion: Dict[str, Any]):
        """Apply experience relaxation suggestion."""
        current_min = self.session_state.get('min_exp', 0)
        current_max = self.session_state.get('max_exp', 10)
        
        # Expand range by 2 years on each side
        new_min = max(0, current_min - 2)
        new_max = min(25, current_max + 2)
        
        self.session_state['min_exp'] = new_min
        self.session_state['max_exp'] = new_max
    
    def _apply_location_relaxation(self, suggestion: Dict[str, Any]):
        """Apply location relaxation suggestion."""
        current_cities = self.session_state.get('current_cities', [])
        preferred_cities = self.session_state.get('preferred_cities', [])
        
        # Add common cities if not already present
        additional_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Pune', 'Hyderabad']
        
        for city in additional_cities:
            if city not in current_cities and city not in preferred_cities:
                preferred_cities.append(city)
                if len(preferred_cities) >= 5:  # Limit to 5 additional cities
                    break
        
        self.session_state['preferred_cities'] = preferred_cities
    
    def _apply_salary_relaxation(self, suggestion: Dict[str, Any]):
        """Apply salary relaxation suggestion."""
        current_max = self.session_state.get('max_salary', 15)
        new_max = min(30, current_max + 5)  # Increase by 5 lakhs, max 30
        self.session_state['max_salary'] = new_max
    
    def _apply_multiple_suggestions(self, suggestions: List[Dict[str, Any]]):
        """Apply multiple relaxation suggestions."""
        applied_count = 0
        
        for suggestion in suggestions:
            try:
                self._apply_relaxation_suggestion(suggestion)
                applied_count += 1
            except Exception as e:
                st.warning(f"Failed to apply {suggestion.get('title', 'suggestion')}: {e}")
        
        if applied_count > 0:
            st.success(f"✅ Applied {applied_count} relaxation suggestions!")
            st.experimental_rerun()
        else:
            st.error("Failed to apply any suggestions")
    
    def _save_relaxation_suggestions(self, suggestions: List[Dict[str, Any]], relaxation_data: Dict[str, Any]):
        """Save relaxation suggestions for later use."""
        try:
            # Store in session state for later access
            self.session_state['saved_relaxation_suggestions'] = {
                'suggestions': suggestions,
                'relaxation_data': relaxation_data,
                'timestamp': str(pd.Timestamp.now())
            }
            
            st.success("💾 Relaxation suggestions saved successfully!")
            
        except Exception as e:
            st.error(f"Failed to save suggestions: {e}")
    
    def _manual_skill_relaxation(self):
        """Manual skill relaxation."""
        current_keywords = self.session_state.get('keywords', [])
        if len(current_keywords) > 2:
            self.session_state['keywords'] = current_keywords[:-1]
            st.success("🔧 Removed one skill requirement")
            st.experimental_rerun()
        else:
            st.warning("Cannot reduce skills further")
    
    def _manual_experience_relaxation(self):
        """Manual experience relaxation."""
        current_min = self.session_state.get('min_exp', 0)
        current_max = self.session_state.get('max_exp', 10)
        
        new_min = max(0, current_min - 1)
        new_max = min(20, current_max + 2)
        
        self.session_state['min_exp'] = new_min
        self.session_state['max_exp'] = new_max
        
        st.success(f"📈 Expanded experience range to {new_min}-{new_max} years")
        st.experimental_rerun()
    
    def _manual_location_relaxation(self):
        """Manual location relaxation."""
        preferred_cities = self.session_state.get('preferred_cities', [])
        if 'Remote' not in preferred_cities:
            preferred_cities.append('Remote')
            self.session_state['preferred_cities'] = preferred_cities
            st.success("🌍 Added remote work option")
            st.experimental_rerun()
        else:
            st.info("Remote work already enabled")
    
    def _manual_salary_relaxation(self):
        """Manual salary relaxation."""
        current_max = self.session_state.get('max_salary', 15)
        new_max = min(25, current_max + 3)
        
        self.session_state['max_salary'] = new_max
        st.success(f"💰 Increased salary range to {new_max} lakhs")
        st.experimental_rerun()
    
    def render_relaxation_in_sidebar(self, relaxation_data: Dict[str, Any]):
        """Render compact relaxation suggestions in sidebar."""
        try:
            if not relaxation_data or not relaxation_data.get("success", False):
                return
            
            suggestions = relaxation_data.get("relaxation_suggestions", [])
            if not suggestions:
                return
            
            st.sidebar.markdown("### 🔄 Quick Relaxation")
            
            # Show top 3 suggestions in compact format
            for i, suggestion in enumerate(suggestions[:3]):
                suggestion_type = suggestion.get('type', 'general')
                title = suggestion.get('title', f'Suggestion {i+1}')
                impact = suggestion.get('impact', 'Unknown impact')
                
                style = self.suggestion_styles.get(suggestion_type, self.suggestion_styles['general'])
                icon = style['icon']
                
                if st.sidebar.button(f"{icon} {title}", key=f"sidebar_relaxation_{i}"):
                    self._apply_relaxation_suggestion(suggestion)
            
            # Quick apply all button
            if st.sidebar.button("🚀 Apply All", key="sidebar_apply_all_relaxation"):
                self._apply_multiple_suggestions(suggestions[:3])
                
        except Exception as e:
            st.sidebar.error(f"Error in relaxation sidebar: {e}")
    
    def show_relaxation_summary(self, relaxation_data: Dict[str, Any]):
        """Show a summary of relaxation results."""
        try:
            suggestions = relaxation_data.get("relaxation_suggestions", [])
            current_count = relaxation_data.get("current_count", 0)
            estimated_increase = relaxation_data.get("estimated_new_count", 0)
            
            if not suggestions:
                return
            
            # Create summary metrics
            total_suggestions = len(suggestions)
            high_confidence_suggestions = len([s for s in suggestions if s.get('confidence', 0) >= 0.8])
            
            st.markdown("#### 📊 Relaxation Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Suggestions", total_suggestions)
            
            with col2:
                st.metric("High Confidence", high_confidence_suggestions)
            
            with col3:
                if estimated_increase > 0:
                    st.metric("Potential Increase", f"+{estimated_increase:,}")
                else:
                    st.metric("Expected Impact", "Significant")
            
            with col4:
                if current_count > 0 and estimated_increase > 0:
                    improvement_pct = int((estimated_increase / current_count) * 100)
                    st.metric("Improvement", f"{improvement_pct}%")
                else:
                    st.metric("Status", "Ready")
            
            # Show suggestion types breakdown
            suggestion_types = {}
            for suggestion in suggestions:
                suggestion_type = suggestion.get('type', 'general')
                suggestion_types[suggestion_type] = suggestion_types.get(suggestion_type, 0) + 1
            
            if suggestion_types:
                st.markdown("**Suggestion Types:**")
                type_cols = st.columns(len(suggestion_types))
                
                for i, (suggestion_type, count) in enumerate(suggestion_types.items()):
                    style = self.suggestion_styles.get(suggestion_type, self.suggestion_styles['general'])
                    icon = style['icon']
                    
                    with type_cols[i]:
                        st.markdown(f"""
                        <div style="text-align: center; padding: 10px;">
                            <div style="font-size: 24px;">{icon}</div>
                            <div style="font-size: 12px; font-weight: bold;">{suggestion_type.replace('_', ' ').title()}</div>
                            <div style="font-size: 14px; color: #666;">{count}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
        except Exception as e:
            st.error(f"Error showing relaxation summary: {e}")
    
    def render_relaxation_history(self):
        """Render history of applied relaxations."""
        if 'relaxation_history' not in self.session_state:
            self.session_state['relaxation_history'] = []
        
        history = self.session_state['relaxation_history']
        
        if not history:
            st.info("No relaxation history available.")
            return
        
        st.markdown("#### 📜 Relaxation History")
        
        for i, entry in enumerate(reversed(history[-5:])):  # Show last 5 entries
            timestamp = entry.get('timestamp', 'Unknown time')
            applied_suggestions = entry.get('applied_suggestions', [])
            
            with st.expander(f"Relaxation {len(history)-i} - {timestamp}"):
                for suggestion in applied_suggestions:
                    suggestion_type = suggestion.get('type', 'general')
                    title = suggestion.get('title', 'Unknown suggestion')
                    impact = suggestion.get('impact', 'Unknown impact')
                    
                    style = self.suggestion_styles.get(suggestion_type, self.suggestion_styles['general'])
                    icon = style['icon']
                    
                    st.markdown(f"**{icon} {title}**")
                    st.markdown(f"*Impact: {impact}*")
                    st.markdown("---")
    
    def get_relaxation_insights(self, relaxation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from relaxation data."""
        try:
            suggestions = relaxation_data.get("relaxation_suggestions", [])
            current_count = relaxation_data.get("current_count", 0)
            estimated_increase = relaxation_data.get("estimated_new_count", 0)
            
            insights = {
                "total_suggestions": len(suggestions),
                "high_impact_suggestions": 0,
                "most_common_type": None,
                "total_potential_increase": estimated_increase,
                "recommendation": "No specific recommendation"
            }
            
            if not suggestions:
                return insights
            
            # Count high-impact suggestions
            insights["high_impact_suggestions"] = len([
                s for s in suggestions if s.get('confidence', 0) >= 0.8
            ])
            
            # Find most common suggestion type
            type_counts = {}
            for suggestion in suggestions:
                suggestion_type = suggestion.get('type', 'general')
                type_counts[suggestion_type] = type_counts.get(suggestion_type, 0) + 1
            
            if type_counts:
                insights["most_common_type"] = max(type_counts, key=type_counts.get)
            
            # Generate recommendation
            if current_count < 10:
                insights["recommendation"] = "Apply all suggestions immediately - very low candidate count"
            elif current_count < 50:
                insights["recommendation"] = "Apply high-confidence suggestions first"
            elif estimated_increase > current_count * 0.5:
                insights["recommendation"] = "Strong potential for improvement - consider applying top suggestions"
            else:
                insights["recommendation"] = "Moderate improvements possible - review suggestions carefully"
            
            return insights
            
        except Exception as e:
            st.error(f"Error generating relaxation insights: {e}")
            return {"error": str(e)}


# Integration helper function for main chat interface
def integrate_relaxation_display_in_chat(session_state: Dict[str, Any], root_agent=None):
    """Helper function to integrate relaxation display in chat interface."""
    
    # Check if we have relaxation data to display
    if session_state.get('current_relaxation_data'):
        relaxation_display = RelaxationDisplay(session_state, root_agent)
        
        # Render in main interface
        relaxation_display.render_relaxation_results(session_state['current_relaxation_data'])
        
        # Also render in sidebar if enabled
        relaxation_display.render_relaxation_in_sidebar(session_state['current_relaxation_data'])
        
        return True
    
    return False