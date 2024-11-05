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
        # Get product recommendations based on summary
        recommendations = await coordinator.get_product_recommendations(summary)
        if recommendations["success"]:
            st.session_state.recommendations = recommendations["recommendations"]
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
    st.subheader("🛍️ Recommended Products")
    
    # Filtering options
    st.markdown("### Filter Options")
    col1, col2 = st.columns(2)
    with col1:
        min_score = st.slider("Minimum Relevance Score", 0, 100, 50)
    with col2:
        categories = list(set(prod["category"] for prod in recommendations))
        selected_category = st.selectbox("Filter by Category", ["All"] + categories)
    
    # Sorting options
    sort_by = st.selectbox("Sort by", ["Relevance Score", "Price (Low to High)", "Price (High to Low)"])
    
    # Filter and sort recommendations
    filtered_recommendations = [
        r for r in recommendations 
        if r["relevance_score"] >= min_score 
        and (selected_category == "All" or r["category"] == selected_category)
    ]
    
    if sort_by == "Price (Low to High)":
        filtered_recommendations.sort(key=lambda x: x["price"])
    elif sort_by == "Price (High to Low)":
        filtered_recommendations.sort(key=lambda x: x["price"], reverse=True)
    else:  # Default: sort by relevance score
        filtered_recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Display recommendations
    if filtered_recommendations:
        for product in filtered_recommendations:
            with st.expander(f"{product['name']} (Score: {product['relevance_score']})"):
                st.markdown(f"**Category:** {product['category'].title()}")
                st.markdown(f"**Price:** ${product['price']:.2f}")
                st.markdown(f"**Description:** {product['description']}")
                st.markdown("**Features:**")
                for feature in product['features']:
                    st.markdown(f"- {feature}")
                st.markdown(f"**Match Explanation:** {product['match_explanation']}")
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
                with st.spinner("Generating summary and recommendations..."):
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
                
                # Display product recommendations if available
                if st.session_state.recommendations:
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
