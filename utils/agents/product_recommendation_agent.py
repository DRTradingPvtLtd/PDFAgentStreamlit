from .base_agent import BaseAgent
import os
from openai import AzureOpenAI
from typing import List, Dict, Optional
import glob
import json
import re

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

    def _scan_files(self, base_dirs=['data', '.']) -> List[Dict]:
        """Scan the filesystem for data description files."""
        data_files = []
        
        for base_dir in base_dirs:
            if os.path.exists(base_dir):
                pattern = os.path.join(base_dir, '**/*.txt')
                for file_path in glob.glob(pattern, recursive=True):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Check if file contains expected sections
                            if any(section in content for section in [
                                "Customer Application Understanding",
                                "Target Product Specifications",
                                "Technical Parameters",
                                "Base Type"
                            ]):
                                sections = self._parse_sections(content)
                                if sections:
                                    data_files.append({
                                        'path': file_path,
                                        'name': os.path.basename(file_path),
                                        'content': content,
                                        'sections': sections,
                                        'size': os.path.getsize(file_path),
                                        'modified': os.path.getmtime(file_path)
                                    })
                    except Exception as e:
                        self.log_action("File reading error", f"Error reading {file_path}: {str(e)}")
        
        return data_files

    def _parse_sections(self, content: str) -> Dict:
        """Parse content into structured sections."""
        sections = {}
        current_section = None
        section_content = []
        
        # Regular expressions for section detection
        section_pattern = re.compile(r'^#+\s*(.*?)\s*$', re.MULTILINE)
        subsection_pattern = re.compile(r'^###\s*(.*?)\s*$', re.MULTILINE)
        
        lines = content.split('\n')
        
        for line in lines:
            section_match = section_pattern.match(line)
            if section_match:
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = section_match.group(1)
                section_content = []
            else:
                if current_section:
                    section_content.append(line)
        
        # Add the last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        return sections

    async def _extract_product_info(self, file_info: Dict) -> Optional[Dict]:
        """Extract structured product information from file content."""
        sections = file_info.get('sections', {})
        
        prompt = f"""
        Analyze the following data description file sections and extract structured product information.
        Focus on technical parameters, specifications, and requirements.

        Sections:
        {json.dumps(sections, indent=2)}

        Return a JSON object with the following structure:
        {{
            "name": "Product/specification name",
            "description": "Comprehensive description",
            "category": "Product category or type",
            "technical_parameters": {{
                "viscosity": "range or specific value",
                "base_type": "identified base type",
                "production_technique": "specified technique",
                "other_parameters": []
            }},
            "customer_applications": [],
            "specifications": {{
                "target": "target specifications",
                "requirements": []
            }},
            "features": []
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1000
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
            if not requirements:
                requirements = await self._extract_requirements(summary)
            
            files = self._scan_files()
            products = []
            
            for file_info in files:
                product_info = await self._extract_product_info(file_info)
                if product_info:
                    products.append(product_info)
            
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
            return {"success": False, "error": str(e)}

    async def _extract_requirements(self, summary: str) -> str:
        """Extract technical requirements from document summary."""
        prompt = f"""
        Based on the following document summary, extract key technical requirements
        and specifications needed for chocolate product matching:

        Summary: {summary}

        Focus on extracting:
        1. Customer application requirements
        2. Technical parameters needed
        3. Base type preferences
        4. Production technique requirements
        5. Specific constraints or specifications

        Please list the requirements in a structured, technical format.
        """

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=500
        )
        
        return response.choices[0].message.content

    async def _match_products(self, requirements: str, products: List[Dict]) -> List[Dict]:
        """Match products based on technical parameters and specifications."""
        prompt = f"""
        Given the following requirements and product specifications, analyze the technical compatibility
        and provide a detailed matching score from 0-100:

        Requirements:
        {requirements}

        Consider these matching criteria:
        1. Base type compatibility
        2. Technical parameter alignment
        3. Customer application suitability
        4. Production technique compatibility
        5. Specification match accuracy

        For each product, provide:
        - Overall compatibility score
        - Technical parameter match details
        - Application suitability analysis
        - Specification alignment details
        """

        recommendations = []
        
        for product in products:
            product_prompt = f"{prompt}\n\nProduct Specifications:\n{json.dumps(product, indent=2)}"
            
            try:
                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[{"role": "user", "content": product_prompt}],
                    temperature=0.0,
                    max_tokens=500
                )
                
                analysis = response.choices[0].message.content
                
                # Extract score and create detailed match explanation
                score_match = re.search(r'(\d{1,3})', analysis)
                score = int(score_match.group(1)) if score_match else 50
                
                recommendations.append({
                    **product,
                    "relevance_score": score,
                    "match_explanation": analysis,
                    "technical_match_details": {
                        "base_type_compatibility": self._extract_compatibility_score(analysis, "base_type"),
                        "parameter_alignment": self._extract_compatibility_score(analysis, "parameter"),
                        "application_suitability": self._extract_compatibility_score(analysis, "application")
                    }
                })
                
            except Exception as e:
                self.log_action("Matching error", f"Error matching product {product.get('name', 'unknown')}: {str(e)}")
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return recommendations

    def _extract_compatibility_score(self, analysis: str, aspect: str) -> int:
        """Extract specific compatibility scores from analysis text."""
        patterns = {
            "base_type": r"base\s+type\s+compatibility:\s*(\d+)",
            "parameter": r"parameter\s+alignment:\s*(\d+)",
            "application": r"application\s+suitability:\s*(\d+)"
        }
        
        if aspect in patterns:
            match = re.search(patterns[aspect], analysis.lower())
            if match:
                return int(match.group(1))
        return 50  # Default score if not found
