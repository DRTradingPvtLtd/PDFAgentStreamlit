from .base_agent import BaseAgent
import os
from openai import AzureOpenAI
from typing import List, Dict
import glob
import json

class ProductRecommendationAgent(BaseAgent):
    """Agent responsible for product recommendations based on document analysis."""
    
    def __init__(self):
        super().__init__("Product Recommendation Agent")
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

    def _scan_files(self, extensions=['.txt', '.md', '.json']) -> List[Dict]:
        """Scan the filesystem for product-related files."""
        products = []
        base_dirs = ['products', 'data', '.']  # Directories to scan
        
        for base_dir in base_dirs:
            if os.path.exists(base_dir):
                for ext in extensions:
                    pattern = os.path.join(base_dir, f'**/*{ext}')
                    for file_path in glob.glob(pattern, recursive=True):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                file_info = {
                                    'path': file_path,
                                    'name': os.path.basename(file_path),
                                    'content': content,
                                    'size': os.path.getsize(file_path),
                                    'modified': os.path.getmtime(file_path)
                                }
                                
                                # Try to parse JSON files
                                if file_path.endswith('.json'):
                                    try:
                                        parsed_content = json.loads(content)
                                        file_info['parsed_content'] = parsed_content
                                    except json.JSONDecodeError:
                                        pass
                                
                                products.append(file_info)
                        except Exception as e:
                            self.log_action("File reading error", f"Error reading {file_path}: {str(e)}")
        
        return products

    async def _extract_product_info(self, file_info: Dict) -> Dict:
        """Extract product information from file content using Azure OpenAI."""
        prompt = f"""
        Analyze the following file content and extract product-related information in a structured format.
        If the content doesn't appear to be product-related, return null.

        File name: {file_info['name']}
        Content: {file_info['content'][:2000]}  # Limit content length

        Return a JSON object with the following structure if product-related:
        {{
            "name": "Product name",
            "description": "Product description",
            "category": "Product category",
            "features": ["feature1", "feature2"],
            "price": estimated_price_if_mentioned_or_null
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            try:
                product_info = json.loads(content)
                if product_info:
                    return {**file_info, **product_info}
            except (json.JSONDecodeError, TypeError):
                pass
            
        except Exception as e:
            self.log_action("Extraction error", str(e))
        
        return None

    async def process(self, summary: str, requirements: str = None) -> dict:
        """Process document summary and requirements to recommend products."""
        try:
            # Extract requirements from summary if not provided
            if not requirements:
                requirements = await self._extract_requirements(summary)
            
            # Scan files and extract product information
            files = self._scan_files()
            products = []
            
            for file_info in files:
                product_info = await self._extract_product_info(file_info)
                if product_info:
                    products.append(product_info)
            
            # Match products based on requirements
            matches = await self._match_products(requirements, products)
            
            return {
                "success": True,
                "recommendations": matches,
                "metadata": {
                    "requirements": requirements,
                    "total_matches": len(matches),
                    "scanned_files": len(files)
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

    async def _match_products(self, requirements: str, products: List[Dict]) -> List[Dict]:
        """Match products based on requirements using content similarity."""
        prompt = f"""
        Given the following user requirements and list of products, analyze the relevance of each product and provide a score from 0-100:

        Requirements: {requirements}

        For each product, consider:
        1. How well the product features match the requirements
        2. The relevance of the product category to the requirements
        3. The completeness of the product information

        Return a brief explanation of why each product matches or doesn't match the requirements.
        """

        recommendations = []
        
        for product in products:
            product_prompt = f"{prompt}\n\nProduct:\n{json.dumps(product, indent=2)}"
            
            try:
                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[{"role": "user", "content": product_prompt}],
                    temperature=0.0,
                    max_tokens=300
                )
                
                analysis = response.choices[0].message.content
                
                # Extract score from analysis (assuming it's mentioned in the text)
                import re
                score_match = re.search(r'(\d{1,3})', analysis)
                score = int(score_match.group(1)) if score_match else 50
                
                recommendations.append({
                    **product,
                    "relevance_score": score,
                    "match_explanation": analysis
                })
                
            except Exception as e:
                self.log_action("Matching error", f"Error matching product {product.get('name', 'unknown')}: {str(e)}")
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return recommendations
