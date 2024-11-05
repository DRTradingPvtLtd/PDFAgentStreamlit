from typing import Dict, List, Optional
import streamlit as st
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AgentStep:
    name: str
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    details: Optional[Dict] = None

class AgentProgressTracker:
    def __init__(self):
        if 'agent_steps' not in st.session_state:
            st.session_state.agent_steps = []
        if 'current_step_index' not in st.session_state:
            st.session_state.current_step_index = 0
    
    def initialize_workflow(self):
        """Initialize the standard workflow steps"""
        st.session_state.agent_steps = [
            AgentStep("Market Segment Identification", "pending", None, None, {}),
            AgentStep("Requirements Extraction", "pending", None, None, {}),
            AgentStep("Phase 1 Search (Strict)", "pending", None, None, {}),
            AgentStep("Phase 2 Search (Relaxed)", "pending", None, None, {}),
            AgentStep("Cross-sell Recommendations", "pending", None, None, {})
        ]
        st.session_state.current_step_index = 0

    def start_step(self, step_index: int, details: Optional[Dict] = None):
        """Mark a step as started"""
        if 0 <= step_index < len(st.session_state.agent_steps):
            step = st.session_state.agent_steps[step_index]
            step.status = "in_progress"
            step.start_time = datetime.now()
            if details:
                step.details = details
            st.session_state.current_step_index = step_index

    def complete_step(self, step_index: int, details: Optional[Dict] = None):
        """Mark a step as completed"""
        if 0 <= step_index < len(st.session_state.agent_steps):
            step = st.session_state.agent_steps[step_index]
            step.status = "completed"
            step.end_time = datetime.now()
            if details:
                step.details.update(details)

    def fail_step(self, step_index: int, error_details: Dict):
        """Mark a step as failed"""
        if 0 <= step_index < len(st.session_state.agent_steps):
            step = st.session_state.agent_steps[step_index]
            step.status = "failed"
            step.end_time = datetime.now()
            step.details = error_details

    def render_progress(self):
        """Render the progress visualization"""
        st.markdown("### 🔍 Search Progress")
        
        for idx, step in enumerate(st.session_state.agent_steps):
            col1, col2 = st.columns([7, 3])
            
            # Status indicator and step name
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌"
            }.get(step.status, "⏳")
            
            with col1:
                st.markdown(f"{status_emoji} **{step.name}**")
                if step.details:
                    with st.expander("Details"):
                        for key, value in step.details.items():
                            st.write(f"**{key}:** {value}")
            
            # Timing information
            with col2:
                if step.start_time:
                    if step.end_time:
                        duration = (step.end_time - step.start_time).total_seconds()
                        st.text(f"Duration: {duration:.1f}s")
                    elif step.status == "in_progress":
                        st.text("In progress...")
            
            # Progress bar
            if step.status == "completed":
                st.progress(1.0)
            elif step.status == "in_progress":
                st.progress(0.5)
            else:
                st.progress(0.0)
