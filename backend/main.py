from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from pathlib import Path

# Add parent directory to system path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.pdf_processor import PDFProcessor
from utils.qa_engine import QAEngine

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize QA Engine
qa_engine = QAEngine()

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not PDFProcessor.validate_pdf(file.file):
        return {"error": "Invalid PDF file"}
    
    try:
        text = PDFProcessor.extract_text(file.file)
        if not text:
            return {"error": "Could not extract text from PDF"}
        
        # Generate summary
        summary = qa_engine.generate_summary(text, "detailed", True)
        
        # Extract requirements
        requirements = qa_engine.extract_requirements(text)
        
        # Find matching products
        product_matches = []
        if requirements:
            product_matches = qa_engine.product_matcher.find_matching_products(requirements)
        
        # Generate sales pitch
        sales_pitch = None
        cross_sell_recommendations = None
        cross_sell_pitch = None
        
        if product_matches:
            sales_pitch = qa_engine.generate_product_pitch(text, requirements)
            
            # Get cross-sell recommendations for top match
            top_match = product_matches[0]
            cross_sell_recommendations = qa_engine.product_matcher.get_cross_sell_recommendations(
                top_match['material_code']
            )
            
            if cross_sell_recommendations:
                cross_sell_pitch = qa_engine.generate_cross_sell_pitch(
                    top_match,
                    cross_sell_recommendations
                )
        
        return {
            "success": True,
            "summary": summary,
            "requirements": requirements,
            "product_matches": product_matches,
            "sales_pitch": sales_pitch,
            "cross_sell_recommendations": cross_sell_recommendations,
            "cross_sell_pitch": cross_sell_pitch
        }
    
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/ask")
async def ask_question(data: dict):
    try:
        question = data.get("question")
        context = data.get("context")
        
        if not question or not context:
            return {"error": "Missing question or context"}
        
        answer = qa_engine.get_answer(context, question)
        return {"answer": answer}
    
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
