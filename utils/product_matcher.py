import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import streamlit as st
from .agents import (
    MarketSegmentAgent,
    RequirementExtractorAgent,
    Phase1SearchAgent,
    Phase2SearchAgent,
    RecommendationAgent
)

class ProductMatchingEngine:
    def __init__(self):
        # Load reference data
        self.classification_data = pd.read_csv('reference_data/01_Classification_New.csv')
        self.technical_params = pd.read_csv('reference_data/01_Technical_parameters_per_Production_Technique.csv')
        self.nutrition_data = pd.read_csv('reference_data/03_Nutrition.csv')
        self.allergen_data = pd.read_csv('reference_data/04_Allergens.csv')
        
        # Initialize agents
        self.market_segment_agent = MarketSegmentAgent()
        self.requirement_extractor = RequirementExtractorAgent()
        self.phase1_search_agent = Phase1SearchAgent(self.classification_data, self.nutrition_data)
        self.phase2_search_agent = Phase2SearchAgent(self.classification_data, self.nutrition_data)
        self.recommendation_agent = RecommendationAgent(self.classification_data, self.nutrition_data)

    def find_matching_products(self, requirements: Dict[str, Union[str, Dict[str, str]]]) -> List[Dict]:
        """
        Find matching products using a multi-phase search approach
        """
        try:
            # Phase 1: Strict search
            phase1_matches, phase1_stats = self.phase1_search_agent.search(requirements)
            
            # If Phase 1 finds sufficient matches, return those
            if len(phase1_matches) >= 3:
                return phase1_matches[:5]  # Return top 5 strict matches
            
            # Phase 2: Relaxed search
            phase2_matches, phase2_stats = self.phase2_search_agent.search(requirements)
            
            # Combine and deduplicate results
            all_matches = {}
            
            # Add Phase 1 matches
            for match in phase1_matches:
                all_matches[match['material_code']] = match
            
            # Add Phase 2 matches
            for match in phase2_matches:
                if match['material_code'] not in all_matches:
                    all_matches[match['material_code']] = match
            
            # Convert back to list and sort by match score
            combined_matches = list(all_matches.values())
            combined_matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            return combined_matches[:5]  # Return top 5 combined matches
            
        except Exception as e:
            st.error(f"Error finding matching products: {str(e)}")
            return []

    def get_cross_sell_recommendations(self, material_code: str) -> List[Dict]:
        """
        Get cross-sell recommendations for a given product
        """
        try:
            return self.recommendation_agent.get_recommendations(material_code)
        except Exception as e:
            st.error(f"Error getting cross-sell recommendations: {str(e)}")
            return []

    def extract_requirements(self, text: str) -> Dict[str, Union[str, Dict[str, str]]]:
        """
        Extract requirements from input text using the RequirementExtractor agent
        """
        try:
            # First identify market segment
            market_segment_info = self.market_segment_agent.identify_market_segment(text)
            
            # Extract detailed requirements
            requirements = self.requirement_extractor.extract_requirements(text)
            
            # Add market segment information to requirements
            if market_segment_info:
                requirements['market_segment'] = market_segment_info.get('segment')
                requirements['application'] = market_segment_info.get('application')
            
            return requirements
            
        except Exception as e:
            st.error(f"Error extracting requirements: {str(e)}")
            return {}

    def refine_requirements(self, requirements: Dict, feedback: str) -> Dict:
        """
        Refine requirements based on feedback
        """
        try:
            return self.requirement_extractor.refine_requirements(requirements, feedback)
        except Exception as e:
            st.error(f"Error refining requirements: {str(e)}")
            return requirements
