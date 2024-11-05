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

    def get_answer(self, context: str, question: str, user_preferences: dict = None) -> str:
        try:
            preferences_context = ""
            if user_preferences:
                preferences_context = f"""
                Consider the following user preferences while answering:
                - Preferred chocolate type: {user_preferences.get('chocolate_type', 'N/A')}
                - Preferred flavor notes: {user_preferences.get('flavor_notes', 'N/A')}
                - Dietary restrictions: {user_preferences.get('dietary_restrictions', 'N/A')}
                - Cocoa percentage preference: {user_preferences.get('cocoa_percentage', 'N/A')}
                """

            prompt = f"""
            Context: {context}
            
            {preferences_context}
            
            Question: {question}
            
            Please provide a concise and accurate answer based on the context above.
            If the question is about chocolate products, consider the user's preferences in your response.
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

    def generate_summary(self, text: str, summary_type: str = "concise", focus_on_chocolate: bool = False) -> str:
        try:
            base_prompts = {
                "concise": "Please provide a brief summary of the following text in 2-3 sentences:",
                "detailed": "Please provide a comprehensive summary of the following text, including main points and key details:",
                "bullet_points": "Please summarize the following text in a bullet-point format, highlighting the key points:"
            }
            
            chocolate_focus = """
            If the text contains information about chocolate products, focus on:
            - Flavor profiles and tasting notes
            - Cocoa content and origins
            - Special ingredients or unique characteristics
            - Production methods and quality indicators
            """ if focus_on_chocolate else ""
            
            prompt = f"""{base_prompts.get(summary_type, base_prompts['concise'])}

            Text: {text}

            {chocolate_focus}
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

    def analyze_chocolate_preferences(self, preferences: dict) -> str:
        try:
            prompt = f"""
            Based on the following chocolate preferences:
            - Preferred chocolate type: {preferences.get('chocolate_type', 'N/A')}
            - Preferred flavor notes: {preferences.get('flavor_notes', 'N/A')}
            - Dietary restrictions: {preferences.get('dietary_restrictions', 'N/A')}
            - Cocoa percentage preference: {preferences.get('cocoa_percentage', 'N/A')}

            Please provide:
            1. A brief analysis of these preferences
            2. Suggested chocolate categories that might appeal to this user
            3. Any special considerations based on dietary restrictions
            """

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,
                max_tokens=500)

            content = response.choices[0].message.content
            return content if content else "Sorry, I couldn't analyze the preferences."

        except Exception as e:
            st.error(f"Error analyzing preferences: {str(e)}")
            return "Sorry, I encountered an error while analyzing preferences."

    def generate_product_pitch(self, context: str, customer_requirements: str, user_preferences: dict = None) -> str:
        try:
            preferences_context = ""
            if user_preferences:
                preferences_context = f"""
                Consider these user preferences:
                - Chocolate type preference: {user_preferences.get('chocolate_type', 'N/A')}
                - Flavor notes preference: {user_preferences.get('flavor_notes', 'N/A')}
                - Dietary restrictions: {user_preferences.get('dietary_restrictions', 'N/A')}
                - Cocoa percentage preference: {user_preferences.get('cocoa_percentage', 'N/A')}
                """

            prompt = f"""
            Product Context: {context}
            
            Customer Requirements: {customer_requirements}
            
            {preferences_context}
            
            Please analyze the product details and create a persuasive sales pitch that:
            1. Highlights key product features that align with the customer requirements and preferences
            2. Addresses specific customer needs and pain points
            3. Emphasizes unique selling propositions, especially regarding chocolate characteristics
            4. Includes a clear call to action
            5. If applicable, mentions how the product aligns with dietary restrictions
            
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
