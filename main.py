import streamlit as st
import asyncio
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

async def process_pdf(coordinator, file):
    """Process PDF file using the coordinator."""
    result = await coordinator.process_pdf(file)
    if result["success"]:
        st.session_state.pdf_text = result["text"]
        return True
    else:
        st.error(f"Error processing PDF: {result.get('error', 'Unknown error')}")
        return False

async def generate_summary(coordinator, text, summary_type):
    """Generate summary using the coordinator."""
    result = await coordinator.generate_summary(text, summary_type)
    if result["success"]:
        return result["summary"]
    else:
        st.error(f"Error generating summary: {result.get('error', 'Unknown error')}")
        return None

async def get_answer(coordinator, context, question):
    """Get answer using the coordinator."""
    result = await coordinator.get_answer(context, question)
    if result["success"]:
        return result["answer"]
    else:
        st.error(f"Error generating answer: {result.get('error', 'Unknown error')}")
        return None

def main():
    st.title("📚 PDF Q&A Assistant")
    st.markdown("""
    Upload a PDF document to get summaries and ask questions about its content.
    The AI will help you understand and explore the document.
    """)

    # Initialize session state
    init_session_state()

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

if __name__ == "__main__":
    main()
