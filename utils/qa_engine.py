import os
from openai import AzureOpenAI
import streamlit as st


class QAEngine:

    def __init__(self):
        azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not azure_api_key or not azure_endpoint:
            raise ValueError(
                "Azure OpenAI API key or endpoint is not set in environment variables")
        
        self.client = AzureOpenAI(
            api_key=azure_api_key,
            api_version="2023-05-15",
            azure_endpoint=azure_endpoint
        )
        self.deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")

    def get_answer(self, context: str, question: str) -> str:
        try:
            prompt = f"""
            Context: {context}
            
            Question: {question}
            
            Please provide a concise and accurate answer based on the context above.
            If the answer cannot be found in the context, please say "I cannot find the answer in the provided text."
            """

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.0,
                max_tokens=500)

            content = response.choices[0].message.content
            return content if content else "Sorry, I couldn't generate an answer."

        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
            return "Sorry, I encountered an error while processing your question."

    def generate_summary(self, text: str, summary_type: str = "concise") -> str:
        try:
            prompt_templates = {
                "concise": "Please provide a brief summary of the following text in 2-3 sentences:",
                "detailed": "Please provide a comprehensive summary of the following text, including main points and key details:",
                "bullet_points": "Please summarize the following text in a bullet-point format, highlighting the key points:"
            }
            
            prompt = f"""{prompt_templates.get(summary_type, prompt_templates['concise'])}

            Text: {text}

            Ensure the summary is clear, accurate, and well-structured."""

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.0,
                max_tokens=1000)

            content = response.choices[0].message.content
            return content if content else "Sorry, I couldn't generate a summary."

        except Exception as e:
            st.error(f"Error generating summary: {str(e)}")
            return "Sorry, I encountered an error while generating the summary."

    def generate_product_pitch(self, context: str, customer_requirements: str) -> str:
        try:
            prompt = f"""
            Product Context: {context}
            
            Customer Requirements: {customer_requirements}
            
            Please analyze the product details and create a persuasive sales pitch that:
            1. Highlights key product features that align with the customer requirements
            2. Addresses specific customer needs and pain points
            3. Emphasizes unique selling propositions
            4. Includes a clear call to action
            
            Format the pitch in a professional and engaging way.
            """

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,
                max_tokens=1000)

            content = response.choices[0].message.content
            return content if content else "Sorry, I couldn't generate a sales pitch."

        except Exception as e:
            st.error(f"Error generating sales pitch: {str(e)}")
            return "Sorry, I encountered an error while generating the sales pitch."
