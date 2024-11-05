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
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'chocolate_type': None,
            'flavor_notes': None,
            'dietary_restrictions': None,
            'cocoa_percentage': None
        }
    if 'product_requirements' not in st.session_state:
        st.session_state.product_requirements = {
            'base_type': None,
            'product_type': None,
            'region': None,
            'technical_params': {}
        }

def update_preferences(key, value):
    st.session_state.user_preferences[key] = value

def update_requirements(key, value):
    st.session_state.product_requirements[key] = value

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

        if st.button("Analyze My Preferences"):
            with st.spinner("Analyzing your preferences..."):
                analysis = st.session_state.qa_engine.analyze_chocolate_preferences(
                    st.session_state.user_preferences
                )
                st.markdown("### Preference Analysis:")
                st.markdown(analysis)

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

    # Product Matching Section
    with st.container():
        st.markdown('<div class="product-matching-section">', unsafe_allow_html=True)
        st.subheader("🔍 Find Matching Products")
        
        col1, col2 = st.columns(2)
        with col1:
            base_type = st.selectbox(
                "Base Type",
                ["Dark", "Milk", "White", "Ruby", "Any"],
                key="base_type",
                on_change=lambda: update_requirements('base_type', st.session_state.base_type)
            )
            
            product_type = st.selectbox(
                "Product Type",
                ["Standard", "Premium", "Sugar-Free", "Vegan", "Any"],
                key="prod_type",
                on_change=lambda: update_requirements('product_type', st.session_state.prod_type)
            )
            
        with col2:
            region = st.selectbox(
                "Region",
                ["EMEA", "NAM", "APAC", "Any"],
                key="region",
                on_change=lambda: update_requirements('region', st.session_state.region)
            )
            
        if st.button("Find Matching Products"):
            requirements = {k: v for k, v in st.session_state.product_requirements.items() 
                          if v not in (None, "Any")}
            
            matches = st.session_state.qa_engine.product_matcher.find_matching_products(
                requirements,
                st.session_state.user_preferences
            )
            
            if matches:
                st.markdown("### Matching Products:")
                for match in matches:
                    with st.expander(f"{match['description']} (Score: {match['match_score']:.2f})"):
                        st.json(match['details'])
            else:
                st.warning("No matching products found.")
                
        st.markdown('</div>', unsafe_allow_html=True)

    # Content Analysis section
    if st.session_state.pdf_text:
        with st.container():
            st.markdown('<div class="qa-section">', unsafe_allow_html=True)
            
            # Document Summary Section
            st.subheader("📝 Document Summary")
            cols = st.columns([3, 1])
            with cols[0]:
                summary_type = st.selectbox(
                    "Select summary type:",
                    ["concise", "detailed", "bullet_points"],
                    format_func=lambda x: x.replace('_', ' ').title()
                )
            with cols[1]:
                focus_on_chocolate = st.checkbox("Focus on Chocolate Content", value=True)
            
            if st.button("Generate Summary"):
                with st.spinner("Generating summary..."):
                    st.session_state.summary = st.session_state.qa_engine.generate_summary(
                        st.session_state.pdf_text,
                        summary_type,
                        focus_on_chocolate
                    )
            
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
                        answer = st.session_state.qa_engine.get_answer(
                            st.session_state.pdf_text,
                            user_question,
                            st.session_state.user_preferences
                        )
                        st.markdown("### Answer:")
                        st.markdown(answer)

            st.divider()

            # Sales Pitch Generator Section
            st.subheader("🎯 Generate Sales Pitch")
            st.markdown("""
            Generate a customized chocolate-focused sales pitch based on the document content and specific customer requirements.
            """)
            
            customer_requirements = st.text_area(
                "Enter customer requirements and pain points:",
                height=100,
                placeholder="Example: Looking for premium dark chocolate gifts for corporate clients with dietary restrictions..."
            )
            
            if st.button("Generate Sales Pitch"):
                if not customer_requirements:
                    st.warning("Please enter customer requirements to generate a pitch.")
                else:
                    with st.spinner("Generating sales pitch..."):
                        pitch = st.session_state.qa_engine.generate_product_pitch(
                            st.session_state.pdf_text,
                            customer_requirements,
                            st.session_state.user_preferences
                        )
                        st.markdown("### Generated Sales Pitch:")
                        st.markdown(pitch)
            
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()