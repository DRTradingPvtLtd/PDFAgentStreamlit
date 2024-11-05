import PyPDF2
from io import BytesIO
import streamlit as st

class PDFProcessor:
    @staticmethod
    def extract_text(pdf_file) -> str:
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.getvalue()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return ""

    @staticmethod
    def validate_pdf(pdf_file) -> bool:
        if pdf_file is None:
            return False
        if pdf_file.type != "application/pdf":
            return False
        return True
