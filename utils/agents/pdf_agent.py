from .base_agent import BaseAgent
import PyPDF2
from io import BytesIO
import streamlit as st

class PDFAgent(BaseAgent):
    """Agent responsible for PDF processing operations."""
    
    def __init__(self):
        super().__init__("PDF Processing Agent")
    
    async def process(self, pdf_file) -> dict:
        """Process PDF file and extract text."""
        try:
            if not self._validate_pdf(pdf_file):
                return {"success": False, "error": "Invalid PDF file"}
            
            text = self._extract_text(pdf_file)
            if not text:
                return {"success": False, "error": "Could not extract text from PDF"}
            
            return {
                "success": True,
                "text": text,
                "metadata": {
                    "filename": pdf_file.name,
                    "size": pdf_file.size
                }
            }
        except Exception as e:
            self.log_action("Error", str(e))
            return {"success": False, "error": str(e)}
    
    def _validate_pdf(self, pdf_file) -> bool:
        """Validate PDF file."""
        if pdf_file is None:
            return False
        if pdf_file.type != "application/pdf":
            return False
        return True
    
    def _extract_text(self, pdf_file) -> str:
        """Extract text from PDF file."""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.getvalue()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            self.log_action("Text extraction error", str(e))
            return ""
