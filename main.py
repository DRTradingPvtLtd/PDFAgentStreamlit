import streamlit as st
import asyncio
import time
from utils.agents.coordinator import AgentCoordinator

# Page configuration
st.set_page_config(
    page_title="PDF Q&A Assistant",
    page_icon="📚",
    layout="wide"
)

# Load custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables."""
    if 'coordinator' not in st.session_state:
        st.session_state.coordinator = AgentCoordinator()
    if 'pdf_text' not in st.session_state:
        st.session_state.pdf_text = None
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'active_agent' not in st.session_state:
        st.session_state.active_agent = None

def display_agent_status():
    """Display the status of all agents."""
    st.markdown('<div class="agent-status">', unsafe_allow_html=True)
    
    agents = ['PDF Agent', 'QA Agent', 'Summary Agent']
    for agent in agents:
        status = "status-active" if st.session_state.active_agent == agent else "status-idle"
        st.markdown(
            f'<div class="status-indicator {status}">'
            f'<span>🤖 {agent}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

def add_to_conversation(actor: str, message: str, message_type: str):
    """Add a message to the conversation history."""
    st.session_state.conversation_history.append({
        'actor': actor,
        'message': message,
        'type': message_type,
        'timestamp': time.strftime('%H:%M:%S')
    })

def display_conversation_history():
    """Display the conversation history."""
    if st.session_state.conversation_history:
        st.markdown('<div class="conversation-history">', unsafe_allow_html=True)
        st.subheader("💬 Conversation History")
        
        for entry in st.session_state.conversation_history:
            if entry['type'] == 'user':
                st.markdown(
                    f'<div class="user-query">'
                    f'<strong>User ({entry["timestamp"]}):</strong><br>{entry["message"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                agent_class = f'{entry["type"]}-agent-response'
                st.markdown(
                    f'<div class="agent-response {agent_class}">'
                    f'<strong>🤖 {entry["actor"]} ({entry["timestamp"]}):</strong><br>{entry["message"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        st.markdown('</div>', unsafe_allow_html=True)

async def process_pdf(coordinator, file):
    """Process PDF file using the coordinator."""
    st.session_state.active_agent = "PDF Agent"
    result = await coordinator.process_pdf(file)
    st.session_state.active_agent = None
    
    if result["success"]:
        st.session_state.pdf_text = result["text"]
        add_to_conversation("PDF Agent", "Successfully processed the PDF file.", "pdf")
        return True
    else:
        error_msg = f"Error processing PDF: {result.get('error', 'Unknown error')}"
        add_to_conversation("PDF Agent", error_msg, "pdf")
        st.error(error_msg)
        return False

async def generate_summary(coordinator, text, summary_type):
    """Generate summary using the coordinator."""
    st.session_state.active_agent = "Summary Agent"
    result = await coordinator.generate_summary(text, summary_type)
    st.session_state.active_agent = None
    
    if result["success"]:
        add_to_conversation("Summary Agent", result["summary"], "summary")
        return result["summary"]
    else:
        error_msg = f"Error generating summary: {result.get('error', 'Unknown error')}"
        add_to_conversation("Summary Agent", error_msg, "summary")
        st.error(error_msg)
        return None

async def get_answer(coordinator, context, question):
    """Get answer using the coordinator."""
    st.session_state.active_agent = "QA Agent"
    result = await coordinator.get_answer(context, question)
    st.session_state.active_agent = None
    
    if result["success"]:
        add_to_conversation("QA Agent", result["answer"], "qa")
        return result["answer"]
    else:
        error_msg = f"Error generating answer: {result.get('error', 'Unknown error')}"
        add_to_conversation("QA Agent", error_msg, "qa")
        st.error(error_msg)
        return None

def main():
    st.title("📚 PDF Q&A Assistant")
    st.markdown("""
    Upload a PDF document to get summaries and ask questions about its content.
    The AI will help you understand and explore the document.
    """)

    # Initialize session state
    init_session_state()
    
    # Display agent status
    display_agent_status()

    # File upload section
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload your PDF file", type=['pdf'])
        
        if uploaded_file is not None:
            if asyncio.run(process_pdf(st.session_state.coordinator, uploaded_file)):
                st.success("PDF processed successfully!")
        st.markdown('</div>', unsafe_allow_html=True)

    # Content Analysis section
    if st.session_state.pdf_text:
        with st.container():
            st.markdown('<div class="qa-section">', unsafe_allow_html=True)
            
            # Document Summary Section
            st.subheader("📝 Document Summary")
            summary_type = st.selectbox(
                "Select summary type:",
                ["concise", "detailed", "bullet_points"],
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            if st.button("Generate Summary"):
                with st.spinner("Generating summary..."):
                    summary = asyncio.run(generate_summary(
                        st.session_state.coordinator,
                        st.session_state.pdf_text,
                        summary_type
                    ))
                    if summary:
                        st.session_state.summary = summary
            
            if st.session_state.summary:
                st.markdown("### Summary:")
                st.markdown(st.session_state.summary)
                st.divider()
            
            # Display text preview
            with st.expander("Preview PDF Content"):
                st.text_area("Extracted Text", st.session_state.pdf_text, height=200)

            # Question input
            st.subheader("❓ Ask Questions")
            user_question = st.text_input("Ask a question about the document:")
            
            if user_question:
                if len(user_question.strip()) < 3:
                    st.warning("Please enter a valid question.")
                else:
                    add_to_conversation("User", user_question, "user")
                    with st.spinner("Generating answer..."):
                        answer = asyncio.run(get_answer(
                            st.session_state.coordinator,
                            st.session_state.pdf_text,
                            user_question
                        ))
                        if answer:
                            st.markdown("### Answer:")
                            st.markdown(answer)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display conversation history
            display_conversation_history()

if __name__ == "__main__":
    main()
