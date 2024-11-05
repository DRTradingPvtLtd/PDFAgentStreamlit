import streamlit as st
from utils.pdf_processor import PDFProcessor
from utils.qa_engine import QAEngine
import os

# Page configuration
st.set_page_config(
    page_title="PDF Q&A Assistant",
    page_icon="📚",
    layout="wide"
)

# Load custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    st.title("📚 PDF Q&A Assistant")
    st.markdown("""
    Upload a PDF document and ask questions about its content.
    The AI will help you find answers within the document.
    """)

    # Initialize session state
    if 'pdf_text' not in st.session_state:
        st.session_state.pdf_text = None
    if 'qa_engine' not in st.session_state:
        st.session_state.qa_engine = QAEngine()

    # File upload section
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload your PDF file", type=['pdf'])
        
        if uploaded_file is not None:
            if PDFProcessor.validate_pdf(uploaded_file):
                with st.spinner("Processing PDF..."):
                    st.session_state.pdf_text = PDFProcessor.extract_text(uploaded_file)
                    if st.session_state.pdf_text:
                        st.success("PDF processed successfully!")
                    else:
                        st.error("Could not extract text from the PDF.")
            else:
                st.error("Please upload a valid PDF file.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Q&A section
    if st.session_state.pdf_text:
        with st.container():
            st.markdown('<div class="qa-section">', unsafe_allow_html=True)
            
            # Display text preview
            with st.expander("Preview PDF Content"):
                st.text_area("Extracted Text", st.session_state.pdf_text, height=200)

            # Question input
            user_question = st.text_input("Ask a question about the document:")
            
            if user_question:
                if len(user_question.strip()) < 3:
                    st.warning("Please enter a valid question.")
                else:
                    with st.spinner("Generating answer..."):
                        answer = st.session_state.qa_engine.get_answer(
                            st.session_state.pdf_text,
                            user_question
                        )
                        st.markdown("### Answer:")
                        st.markdown(answer)
            
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
