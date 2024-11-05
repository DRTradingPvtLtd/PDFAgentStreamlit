from .base_agent import BaseAgent
import json
from typing import List, Dict
import os
from openai import AzureOpenAI

class ProductRecommendationAgent(BaseAgent):
    """Agent responsible for product recommendations based on document analysis."""
    
    def __init__(self):
        super().__init__("Product Recommendation Agent")
        self._initialize_azure_client()
        self._initialize_product_database()
    
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

    def _initialize_product_database(self):
        """Initialize mock product database."""
        self.products = [
            {
                "id": "1",
                "name": "Professional PDF Reader",
                "description": "Advanced PDF reading and annotation software",
                "category": "software",
                "price": 99.99,
                "features": ["PDF editing", "annotations", "OCR capabilities"]
            },
            {
                "id": "2",
                "name": "Document Scanner Pro",
                "description": "High-speed document scanner with OCR",
                "category": "hardware",
                "price": 299.99,
                "features": ["OCR", "wireless scanning", "cloud integration"]
            },
            {
                "id": "3",
                "name": "Cloud Storage Plus",
                "description": "Secure cloud storage for documents",
                "category": "service",
                "price": 9.99,
                "features": ["document storage", "sharing", "version control"]
            }
        ]

    async def process(self, summary: str, requirements: str = None) -> dict:
        """Process document summary and requirements to recommend products."""
        try:
            # Extract requirements from summary if not provided
            if not requirements:
                requirements = await self._extract_requirements(summary)
            
            # Match products based on requirements
            matches = await self._match_products(requirements)
            
            return {
                "success": True,
                "recommendations": matches,
                "metadata": {
                    "requirements": requirements,
                    "total_matches": len(matches)
                }
            }
        except Exception as e:
            self.log_action("Error", str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def _extract_requirements(self, summary: str) -> str:
        """Extract requirements from document summary using Azure OpenAI."""
        prompt = f"""
        Based on the following document summary, extract key requirements or needs that could be addressed by products or services:

        Summary: {summary}

        Please list the key requirements in a clear, concise format.
        """

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=300
        )
        
        return response.choices[0].message.content

    async def _match_products(self, requirements: str) -> List[Dict]:
        """Match products based on requirements."""
        prompt = f"""
        Given the following user requirements and product database, rank the products by relevance and provide a score from 0-100:

        Requirements: {requirements}

        Products: {json.dumps(self.products, indent=2)}

        For each product, return a JSON object with the product details and a relevance score.
        Include a brief explanation of why the product matches the requirements.
        """

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1000
        )

        # Process the response to create structured recommendations
        recommendations = []
        for product in self.products:
            match_score = self._calculate_match_score(product, requirements)
            recommendations.append({
                **product,
                "relevance_score": match_score,
                "match_explanation": f"Product features align with requirements: {', '.join(product['features'])}"
            })
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x['relevance_score'], reverse=True)
        return recommendations

    def _calculate_match_score(self, product: Dict, requirements: str) -> int:
        """Calculate a simple match score based on feature overlap."""
        # Simple scoring mechanism - can be enhanced with more sophisticated logic
        score = 50  # Base score
        
        # Check if any product features are mentioned in requirements
        requirement_words = requirements.lower().split()
        for feature in product['features']:
            if feature.lower() in requirement_words:
                score += 15
                
        return min(100, score)  # Cap score at 100
