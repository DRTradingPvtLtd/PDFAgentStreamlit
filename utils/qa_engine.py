import os
from openai import OpenAI
import streamlit as st

class QAEngine:
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is not set in environment variables")
        self.client = OpenAI(api_key=api_key)

    def get_answer(self, context: str, question: str) -> str:
        try:
            prompt = f"""
            Context: {context}
            
            Question: {question}
            
            Please provide a concise and accurate answer based on the context above.
            If the answer cannot be found in the context, please say "I cannot find the answer in the provided text."
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",  # Using gpt-4 for complex tasks
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            return content if content else "Sorry, I couldn't generate an answer."
            
        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
            return "Sorry, I encountered an error while processing your question."
