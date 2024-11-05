import streamlit as st
from utils.pdf_processor import PDFProcessor
from utils.qa_engine import QAEngine
import os

# Page configuration
st.set_page_config(
    page_title="Chocolate PDF Q&A Assistant",
    page_icon="🍫",
    layout="wide"
)

# Load custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def initialize_session_state():
    if 'pdf_text' not in st.session_state:
        st.session_state.pdf_text = None
    if 'qa_engine' not in st.session_state:
        st.session_state.qa_engine = QAEngine()
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'extracted_requirements' not in st.session_state:
        st.session_state.extracted_requirements = None
    if 'product_matches' not in st.session_state:
        st.session_state.product_matches = None
    if 'sales_pitch' not in st.session_state:
        st.session_state.sales_pitch = None
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'chocolate_type': None,
            'flavor_notes': None,
            'dietary_restrictions': None,
            'cocoa_percentage': None
        }

def update_preferences(key, value):
    st.session_state.user_preferences[key] = value

def process_uploaded_document(pdf_text):
    """Process uploaded document and generate analysis"""
    with st.spinner("Analyzing document..."):
        # Generate summary
        st.session_state.summary = st.session_state.qa_engine.generate_summary(
            pdf_text, "detailed", True)
        
        # Extract requirements
        st.session_state.extracted_requirements = st.session_state.qa_engine.extract_requirements(
            pdf_text)
        
        # Find matching products
        if st.session_state.extracted_requirements:
            st.session_state.product_matches = st.session_state.qa_engine.product_matcher.find_matching_products(
                st.session_state.extracted_requirements,
                st.session_state.user_preferences
            )
            
            # Generate sales pitch
            if st.session_state.product_matches:
                st.session_state.sales_pitch = st.session_state.qa_engine.generate_product_pitch(
                    pdf_text,
                    st.session_state.extracted_requirements,
                    st.session_state.user_preferences
                )

def main():
    st.title("🍫 Chocolate PDF Q&A Assistant")
    st.markdown("""
    Upload a PDF document to analyze chocolate-related content, get summaries, and ask questions.
    The AI will help you understand and explore the document while considering your chocolate preferences.
    """)

    initialize_session_state()

    # User Preferences Section
    with st.sidebar:
        st.header("🎯 Your Chocolate Preferences")
        chocolate_type = st.selectbox(
            "Preferred Chocolate Type",
            ["Dark", "Milk", "White", "Ruby", "No Preference"],
            key="choc_type",
            on_change=lambda: update_preferences('chocolate_type', st.session_state.choc_type)
        )

        flavor_notes = st.multiselect(
            "Preferred Flavor Notes",
            ["Fruity", "Nutty", "Floral", "Spicy", "Caramel", "Vanilla", "Earthy"],
            key="flavors",
            on_change=lambda: update_preferences('flavor_notes', st.session_state.flavors)
        )

        dietary_restrictions = st.multiselect(
            "Dietary Restrictions",
            ["Vegan", "Sugar-Free", "Gluten-Free", "Nut-Free", "Dairy-Free", "None"],
            key="diet",
            on_change=lambda: update_preferences('dietary_restrictions', st.session_state.diet)
        )

        cocoa_percentage = st.slider(
            "Preferred Cocoa Percentage",
            min_value=30,
            max_value=100,
            value=70,
            step=5,
            key="cocoa",
            on_change=lambda: update_preferences('cocoa_percentage', st.session_state.cocoa)
        )

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
                        # Automatically process the document
                        process_uploaded_document(st.session_state.pdf_text)
                    else:
                        st.error("Could not extract text from the PDF.")
            else:
                st.error("Please upload a valid PDF file.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Display Analysis Results
    if st.session_state.pdf_text:
        with st.container():
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            
            # Document Summary
            st.subheader("📝 Document Summary")
            if st.session_state.summary:
                st.markdown(st.session_state.summary)
            st.divider()
            
            # Extracted Requirements
            st.subheader("🎯 Extracted Requirements")
            if st.session_state.extracted_requirements:
                st.json(st.session_state.extracted_requirements)
            st.divider()
            
            # Matching Products
            st.subheader("🔍 Matching Products")
            if st.session_state.product_matches:
                for match in st.session_state.product_matches:
                    with st.expander(f"{match['description']} (Score: {match['match_score']:.2f})"):
                        st.json(match['details'])
            st.divider()
            
            # Sales Pitch
            st.subheader("💼 Generated Sales Pitch")
            if st.session_state.sales_pitch:
                st.markdown(st.session_state.sales_pitch)
            st.divider()

            # Question & Answer Section
            st.subheader("❓ Ask Questions")
            user_question = st.text_input("Ask a question about the document:")
            
            if user_question:
                if len(user_question.strip()) < 3:
                    st.warning("Please enter a valid question.")
                else:
                    with st.spinner("Generating answer..."):
                        answer = st.session_state.qa_engine.get_answer(
                            st.session_state.pdf_text,
                            user_question,
                            st.session_state.user_preferences
                        )
                        st.markdown("### Answer:")
                        st.markdown(answer)
            
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
