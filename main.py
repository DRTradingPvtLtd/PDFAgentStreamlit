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
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    if 'recommendation_error' not in st.session_state:
        st.session_state.recommendation_error = None

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
        summary = result["summary"]
        st.session_state.summary = summary
        
        # Get product recommendations based on summary
        with st.spinner("Generating product recommendations..."):
            recommendations = await coordinator.get_product_recommendations(summary)
            if recommendations["success"]:
                st.session_state.recommendations = recommendations["recommendations"]
                st.session_state.recommendation_error = None
            else:
                st.session_state.recommendation_error = recommendations.get("error", "Unknown error")
        return summary
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

def display_recommendations(recommendations):
    """Display product recommendations with filtering and sorting options."""
    if not recommendations:
        st.warning("No product recommendations available.")
        return

    st.subheader("🛍️ Product Recommendations")
    
    # Filtering options
    with st.expander("Filter and Sort Options", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            min_score = st.slider("Minimum Relevance Score", 0, 100, 50)
        with col2:
            categories = list(set(prod.get("category", "Unknown") for prod in recommendations))
            selected_category = st.selectbox("Filter by Category", ["All"] + categories)
        
        sort_options = {
            "Relevance Score (High to Low)": lambda x: (-x.get("relevance_score", 0)),
            "Base Type Compatibility": lambda x: (-x.get("technical_match_details", {}).get("base_type_compatibility", 0)),
            "Parameter Alignment": lambda x: (-x.get("technical_match_details", {}).get("parameter_alignment", 0)),
            "Application Suitability": lambda x: (-x.get("technical_match_details", {}).get("application_suitability", 0))
        }
        sort_by = st.selectbox("Sort by", list(sort_options.keys()))
    
    # Filter recommendations
    filtered_recommendations = [
        r for r in recommendations 
        if r.get("relevance_score", 0) >= min_score 
        and (selected_category == "All" or r.get("category") == selected_category)
    ]
    
    # Sort recommendations
    filtered_recommendations.sort(key=sort_options[sort_by])
    
    # Display recommendations
    if filtered_recommendations:
        for idx, product in enumerate(filtered_recommendations, 1):
            with st.expander(
                f"#{idx} {product.get('name', 'Unnamed Product')} "
                f"(Score: {product.get('relevance_score', 0)})",
                expanded=idx == 1
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Description:** {product.get('description', 'No description available')}")
                    st.markdown("**Technical Parameters:**")
                    tech_params = product.get("technical_parameters", {})
                    for param, value in tech_params.items():
                        st.markdown(f"- {param.title()}: {value}")
                    
                    if product.get("features"):
                        st.markdown("**Features:**")
                        for feature in product["features"]:
                            st.markdown(f"- {feature}")
                
                with col2:
                    st.markdown("**Match Details:**")
                    tech_match = product.get("technical_match_details", {})
                    for aspect, score in tech_match.items():
                        st.progress(score/100, text=f"{aspect.replace('_', ' ').title()}: {score}%")
            
            if idx < len(filtered_recommendations):
                st.divider()
    else:
        st.info("No products match the current filters.")

def main():
    st.title("📚 PDF Q&A Assistant")
    st.markdown("""
    Upload a PDF document to get summaries, ask questions about its content, and receive relevant product recommendations.
    The AI will help you understand and explore the document while suggesting products that match your needs.
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
                
                # Display recommendations or error
                if st.session_state.recommendation_error:
                    st.error(f"Error generating recommendations: {st.session_state.recommendation_error}")
                elif st.session_state.recommendations:
                    display_recommendations(st.session_state.recommendations)
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
