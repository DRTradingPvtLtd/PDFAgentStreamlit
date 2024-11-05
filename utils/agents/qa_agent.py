import os
from openai import AzureOpenAI
import streamlit as st
from .base_agent import BaseAgent

class QAAgent(BaseAgent):
    """Agent responsible for question answering operations."""
    
    def __init__(self):
        super().__init__("Q&A Agent")
        self._initialize_azure_client()
    
    def _initialize_azure_client(self):
        """Initialize Azure OpenAI client."""
        azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        
        if not azure_api_key or not azure_endpoint:
            raise ValueError("Azure OpenAI API key or endpoint is not set")
        
        self.client = AzureOpenAI(
            api_key=azure_api_key,
            api_version="2023-05-15",
            azure_endpoint=azure_endpoint
        )
        self.deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    async def process(self, context: str, question: str) -> dict:
        """Process a question and generate an answer."""
        try:
            prompt = self._create_qa_prompt(context, question)
            response = await self._get_completion(prompt)
            
            return {
                "success": True,
                "answer": response,
                "metadata": {
                    "model": self.deployment_name,
                    "question": question
                }
            }
        except Exception as e:
            self.log_action("Error", str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_qa_prompt(self, context: str, question: str) -> str:
        """Create prompt for Q&A."""
        return f"""
        Context: {context}
        
        Question: {question}
        
        Please provide a concise and accurate answer based on the context above.
        If the answer cannot be found in the context, please say "I cannot find the answer in the provided text."
        """
    
    async def _get_completion(self, prompt: str) -> str:
        """Get completion from Azure OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.0,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            self.log_action("Completion error", str(e))
            raise
