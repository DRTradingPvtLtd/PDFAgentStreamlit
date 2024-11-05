from typing import Dict, List, Optional
import pandas as pd
from openai import AzureOpenAI
import os

class MarketSegmentAgent:
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
        
        # Market segments and their applications
        self.market_segments = {
            'Confectionery': ['Tablets', 'Pralines', 'Countlines', 'Protein Bars'],
            'Bakery': ['Butter cakes', 'Celebration cakes', 'Laminated pastries'],
            'Ice Cream': ['Ice cream bars', 'Ice cream cones', 'Ice cream sandwiches'],
            'Desserts': ['Frozen desserts', 'Spoonable desserts', 'Yogurt applications']
        }

    def identify_market_segment(self, text: str) -> Dict[str, str]:
        """
        Identify the market segment and specific application from the input text.
        Returns a dictionary with 'segment' and 'application' keys.
        """
        try:
            prompt = f"""
            Analyze the following text and identify the chocolate product's market segment and specific application.
            Focus on these market segments and their applications:
            {self.market_segments}

            Return ONLY a valid JSON with two fields:
            {{
                "segment": "identified market segment",
                "application": "specific application within that segment"
            }}

            Text to analyze:
            {text}

            If uncertain, return the most likely match based on the context.
            """

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=150
            )

            content = response.choices[0].message.content.strip()
            
            # Clean up JSON string if needed
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            import json
            result = json.loads(content.strip())
            
            # Validate the result against known segments and applications
            if result['segment'] in self.market_segments:
                if result['application'] in self.market_segments[result['segment']]:
                    return result
                else:
                    # If application doesn't match exactly, return the segment with the first application
                    return {
                        'segment': result['segment'],
                        'application': self.market_segments[result['segment']][0]
                    }
            
            # Default to Confectionery if no clear match
            return {
                'segment': 'Confectionery',
                'application': 'Tablets'
            }

        except Exception as e:
            print(f"Error in market segment identification: {str(e)}")
            # Return default values if there's an error
            return {
                'segment': 'Confectionery',
                'application': 'Tablets'
            }

    def get_related_applications(self, segment: str) -> List[str]:
        """Get all related applications for a given market segment"""
        return self.market_segments.get(segment, [])

    def validate_segment_application(self, segment: str, application: str) -> bool:
        """Validate if the application belongs to the given segment"""
        return segment in self.market_segments and application in self.market_segments[segment]
