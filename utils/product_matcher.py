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
from .agent_progress import AgentProgressTracker
import os
from pathlib import Path

class ProductMatchingEngine:
    def __init__(self):
        # Get the absolute path to the reference_data directory
        base_dir = Path(__file__).parent.parent
        reference_data_dir = base_dir / 'reference_data'

        # Load reference data with absolute paths
        self.classification_data = pd.read_csv(reference_data_dir / '01_Classification_New.csv')
        self.technical_params = pd.read_csv(reference_data_dir / '01_Technical_parameters_per_Production_Technique.csv')
        self.nutrition_data = pd.read_csv(reference_data_dir / '03_Nutrition.csv')
        self.allergen_data = pd.read_csv(reference_data_dir / '04_Allergens.csv')
        
        # Initialize agents
        self.market_segment_agent = MarketSegmentAgent()
        self.requirement_extractor = RequirementExtractorAgent()
        self.phase1_search_agent = Phase1SearchAgent(self.classification_data, self.nutrition_data)
        self.phase2_search_agent = Phase2SearchAgent(self.classification_data, self.nutrition_data)
        self.recommendation_agent = RecommendationAgent(self.classification_data, self.nutrition_data)
        
        # Initialize progress tracker
        self.progress_tracker = AgentProgressTracker()

    def find_matching_products(self, requirements: Dict[str, Union[str, Dict[str, str]]]) -> List[Dict]:
        """
        Find matching products using a multi-phase search approach
        """
        try:
            # Initialize workflow
            self.progress_tracker.initialize_workflow()
            
            # Phase 0: Market Segment Identification
            self.progress_tracker.start_step(0)
            market_info = self.market_segment_agent.identify_market_segment(str(requirements))
            self.progress_tracker.complete_step(0, {
                "Identified Segment": market_info.get('segment', 'Unknown'),
                "Application": market_info.get('application', 'Unknown')
            })
            
            # Phase 1: Strict search
            self.progress_tracker.start_step(2, {"Search Type": "Strict matching"})
            phase1_matches, phase1_stats = self.phase1_search_agent.search(requirements)
            
            phase1_details = {
                "Initial candidates": phase1_stats.get('initial_count', 0),
                "Final matches": len(phase1_matches),
                "Top match score": f"{phase1_matches[0]['match_score']:.2f}" if phase1_matches else "N/A"
            }
            self.progress_tracker.complete_step(2, phase1_details)
            
            # If Phase 1 finds sufficient matches, skip Phase 2
            if len(phase1_matches) >= 3:
                self.progress_tracker.start_step(3)
                self.progress_tracker.complete_step(3, {"Status": "Skipped - Sufficient matches found in Phase 1"})
                matches = phase1_matches[:5]
            else:
                # Phase 2: Relaxed search
                self.progress_tracker.start_step(3, {"Search Type": "Relaxed matching"})
                phase2_matches, phase2_stats = self.phase2_search_agent.search(requirements)
                
                phase2_details = {
                    "Initial candidates": phase2_stats.get('initial_count', 0),
                    "Final matches": len(phase2_matches),
                    "Top match score": f"{phase2_matches[0]['match_score']:.2f}" if phase2_matches else "N/A",
                    "Relaxation criteria": str(phase2_stats.get('relaxed_requirements', {}))
                }
                self.progress_tracker.complete_step(3, phase2_details)
                
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
                matches = list(all_matches.values())
                matches.sort(key=lambda x: x['match_score'], reverse=True)
                matches = matches[:5]  # Return top 5 combined matches
            
            # Generate cross-sell recommendations for top match
            if matches:
                self.progress_tracker.start_step(4)
                top_match = matches[0]
                cross_sell_recs = self.recommendation_agent.get_recommendations(top_match['material_code'])
                
                cross_sell_details = {
                    "Base product": top_match['description'],
                    "Number of recommendations": len(cross_sell_recs),
                    "Top compatibility score": f"{cross_sell_recs[0]['compatibility_score']:.2f}" if cross_sell_recs else "N/A"
                }
                self.progress_tracker.complete_step(4, cross_sell_details)
            
            return matches
            
        except Exception as e:
            st.error(f"Error finding matching products: {str(e)}")
            current_step = st.session_state.get('current_step_index', 0)
            self.progress_tracker.fail_step(current_step, {"Error": str(e)})
            return []

    def get_cross_sell_recommendations(self, material_code: str) -> List[Dict]:
        """Get cross-sell recommendations for a given product"""
        try:
            return self.recommendation_agent.get_recommendations(material_code)
        except Exception as e:
            st.error(f"Error getting cross-sell recommendations: {str(e)}")
            return []

    def extract_requirements(self, text: str) -> Dict[str, Union[str, Dict[str, str]]]:
        """Extract requirements from input text using the RequirementExtractor agent"""
        try:
            # Start requirements extraction step
            self.progress_tracker.start_step(1)
            
            # First identify market segment
            market_segment_info = self.market_segment_agent.identify_market_segment(text)
            
            # Extract detailed requirements
            requirements = self.requirement_extractor.extract_requirements(text)
            
            # Add market segment information to requirements
            if market_segment_info:
                requirements['market_segment'] = market_segment_info.get('segment')
                requirements['application'] = market_segment_info.get('application')
            
            # Complete requirements extraction step
            self.progress_tracker.complete_step(1, {
                "Identified requirements": len(requirements),
                "Market segment": requirements.get('market_segment', 'Unknown'),
                "Application": requirements.get('application', 'Unknown')
            })
            
            return requirements
            
        except Exception as e:
            st.error(f"Error extracting requirements: {str(e)}")
            self.progress_tracker.fail_step(1, {"Error": str(e)})
            return {}

    def refine_requirements(self, requirements: Dict, feedback: str) -> Dict:
        """Refine requirements based on feedback"""
        try:
            return self.requirement_extractor.refine_requirements(requirements, feedback)
        except Exception as e:
            st.error(f"Error refining requirements: {str(e)}")
            return requirements

    def render_progress(self):
        """Render the current progress"""
        self.progress_tracker.render_progress()
