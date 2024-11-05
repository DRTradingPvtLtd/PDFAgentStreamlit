from typing import Dict, List, Optional, Union
from openai import AzureOpenAI
import os
import json

class RequirementExtractorAgent:
    def __init__(self):
        azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not azure_api_key or not azure_endpoint:
            raise ValueError("Azure OpenAI API key or endpoint is not set in environment variables")
        
        self.client = AzureOpenAI(
            api_key=azure_api_key,
            api_version="2023-05-15",
            azure_endpoint=azure_endpoint
        )
        self.deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")

    def extract_requirements(self, text: str) -> Dict[str, Union[str, Dict[str, str]]]:
        """
        Extract detailed product requirements from the input text.
        Returns a structured dictionary of requirements.
        """
        try:
            prompt = f"""
            Analyze the following text and extract specific chocolate product requirements.
            Return ONLY a valid JSON object with these fields (include only if explicitly mentioned or strongly implied):
            {{
                "base_type": "preferred chocolate base type (dark, milk, white, ruby)",
                "product_type": "type of product (standard, premium, sugar-free)",
                "delivery_format": "required format (drops, block, callets, easymelt)",
                "technical_specs": {{
                    "viscosity": "target viscosity if mentioned",
                    "fineness": "target fineness if mentioned",
                    "ph": "target pH if mentioned"
                }},
                "min_protein_percentage": "minimum protein content if mentioned",
                "region": "target region if mentioned (EMEA, NAM, APAC)",
                "special_requirements": "any special requirements like dietary restrictions"
            }}

            Text to analyze:
            {text}

            Ensure all numerical values are provided as numbers without units.
            """

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()
            
            # Clean up JSON string if needed
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            requirements = json.loads(content.strip())
            return self._validate_requirements(requirements)

        except Exception as e:
            print(f"Error in requirement extraction: {str(e)}")
            return {}

    def _validate_requirements(self, requirements: Dict) -> Dict:
        """Validate and clean extracted requirements"""
        valid_requirements = {}
        
        # Validate base type
        if 'base_type' in requirements:
            base_type = requirements['base_type'].lower()
            if base_type in ['dark', 'milk', 'white', 'ruby']:
                valid_requirements['base_type'] = base_type.capitalize()

        # Validate product type
        if 'product_type' in requirements:
            product_type = requirements['product_type'].lower()
            if product_type in ['standard', 'premium', 'sugar-free']:
                valid_requirements['product_type'] = product_type.capitalize()

        # Validate delivery format
        if 'delivery_format' in requirements:
            delivery_format = requirements['delivery_format'].lower()
            if delivery_format in ['drops', 'block', 'callets', 'easymelt']:
                valid_requirements['delivery_format'] = delivery_format.capitalize()

        # Validate technical specs
        if 'technical_specs' in requirements:
            valid_specs = {}
            for spec, value in requirements['technical_specs'].items():
                try:
                    if value and value != "":
                        valid_specs[spec] = float(str(value).replace(',', '.'))
                except (ValueError, TypeError):
                    continue
            if valid_specs:
                valid_requirements['technical_specs'] = valid_specs

        # Validate protein percentage
        if 'min_protein_percentage' in requirements:
            try:
                protein = float(str(requirements['min_protein_percentage']).replace(',', '.'))
                if 0 < protein <= 100:
                    valid_requirements['min_protein_percentage'] = protein
            except (ValueError, TypeError):
                pass

        # Validate region
        if 'region' in requirements:
            region = requirements['region'].upper()
            if region in ['EMEA', 'NAM', 'APAC']:
                valid_requirements['region'] = region

        # Include special requirements if present
        if 'special_requirements' in requirements and requirements['special_requirements']:
            valid_requirements['special_requirements'] = requirements['special_requirements']

        return valid_requirements

    def refine_requirements(self, requirements: Dict, feedback: str) -> Dict:
        """
        Refine requirements based on feedback
        """
        try:
            prompt = f"""
            Current requirements:
            {json.dumps(requirements, indent=2)}

            Feedback to incorporate:
            {feedback}

            Update the requirements based on the feedback. Return ONLY a valid JSON object with the same structure
            as the current requirements, but with updates based on the feedback.
            """

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()
            
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            updated_requirements = json.loads(content.strip())
            return self._validate_requirements(updated_requirements)

        except Exception as e:
            print(f"Error in requirement refinement: {str(e)}")
            return requirements
