import os
from openai import AzureOpenAI
import streamlit as st
import json
from typing import Dict, List, Optional, Union
from .product_matcher import ProductMatchingEngine

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
        self.product_matcher = ProductMatchingEngine()

    def extract_requirements(self, text: str) -> Dict[str, Union[str, Dict[str, str]]]:
        """Extract product requirements from the document text"""
        try:
            prompt = f"""
            Please analyze the following document and extract chocolate product requirements.
            Return ONLY a valid JSON object with these fields (only include fields that are explicitly mentioned or strongly implied):
            {{
                "base_type": "preferred chocolate base type (dark, milk, white, ruby)",
                "product_type": "type of product needed (standard, premium, sugar-free)",
                "technical_specs": {{"key": "value"}},
                "region": "target region if mentioned (EMEA, NAM, APAC)",
                "special_requirements": "any special requirements or restrictions"
            }}

            Document text:
            {text}

            Ensure the response is a properly formatted JSON object.
            """

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.0,
                max_tokens=500)

            content = response.choices[0].message.content.strip()
            
            # Clean up the response if needed
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Validate JSON before parsing
            try:
                requirements = json.loads(content)
                return requirements
            except json.JSONDecodeError as je:
                st.error(f"Error parsing JSON response: {str(je)}")
                return {}

        except Exception as e:
            st.error(f"Error extracting requirements: {str(e)}")
            return {}

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

    def generate_product_pitch(self, context: str, requirements: Dict[str, Union[str, Dict[str, str]]]) -> str:
        try:
            requirements_str = "\n".join([f"- {k}: {v}" for k, v in requirements.items() if v])

            prompt = f"""
            Product Context: {context}
            
            Requirements:
            {requirements_str}
            
            Please create a persuasive sales pitch that:
            1. Highlights key product features that align with the extracted requirements
            2. Addresses specific customer needs and pain points
            3. Emphasizes unique selling propositions, especially regarding chocolate characteristics
            4. Includes relevant technical specifications and quality indicators
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

    def generate_cross_sell_pitch(self, main_product: Dict[str, Union[str, Dict]], complementary_products: List[Dict[str, Union[str, Dict]]]) -> str:
        """Generate a compelling cross-sell pitch for product combinations"""
        try:
            # Format product information
            main_product_info = (
                f"Main Product: {main_product['description']}\n"
                f"Base Type: {main_product['details']['base_type']}\n"
                f"Product Type: {main_product['details']['product_type']}"
            )
            
            complementary_info = []
            for prod in complementary_products:
                pairing_suggestions = "\n".join([f"  - {s}" for s in prod['pairing_suggestions']])
                info = (
                    f"Complementary Product: {prod['description']}\n"
                    f"Compatibility Score: {prod['compatibility_score']:.2f}\n"
                    f"Suggested Pairings:\n{pairing_suggestions}"
                )
                complementary_info.append(info)
            
            complementary_products_str = "\n\n".join(complementary_info)

            prompt = f"""
            Create a compelling cross-sell pitch for the following chocolate product combination:

            {main_product_info}

            Recommended Combinations:
            {complementary_products_str}

            Please create an engaging pitch that:
            1. Highlights the synergies between the main product and each complementary product
            2. Emphasizes how the combinations enhance the customer's chocolate experience
            3. Suggests creative ways to use the products together
            4. Mentions any technical advantages of the combinations
            5. Includes specific pairing recommendations and serving suggestions
            
            Format the pitch in sections:
            1. Introduction highlighting the main product
            2. Individual sections for each complementary pairing
            3. Conclusion emphasizing the value of the combined offering
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
            return content if content else "Sorry, I couldn't generate a cross-sell pitch."

        except Exception as e:
            st.error(f"Error generating cross-sell pitch: {str(e)}")
            return "Sorry, I encountered an error while generating the cross-sell pitch."
