import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union

class ProductMatchingEngine:
    def __init__(self):
        # Load and process reference data
        self.classification_data = pd.read_csv('reference_data/01_Classification_New.csv')
        self.technical_params = pd.read_csv('reference_data/01_Technical_parameters_per_Production_Technique.csv')
        self.nutrition_data = pd.read_csv('reference_data/03_Nutrition.csv')
        self.allergen_data = pd.read_csv('reference_data/04_Allergens.csv')
        
        # Initialize mappings and similarity matrices
        self._init_mappings()
    
    def _init_mappings(self):
        """Initialize internal mappings and similarity matrices"""
        # Base type similarity matrix
        self.base_type_similarity = {
            'Dark': {'Dark': 1.0, 'Milk': 0.3, 'White': 0.1, 'Ruby': 0.2},
            'Milk': {'Dark': 0.3, 'Milk': 1.0, 'White': 0.6, 'Ruby': 0.5},
            'White': {'Dark': 0.1, 'White': 1.0, 'Milk': 0.6, 'Ruby': 0.4},
            'Ruby': {'Dark': 0.2, 'Ruby': 1.0, 'Milk': 0.5, 'White': 0.4}
        }
        
        # Product type similarity matrix
        self.product_type_similarity = {
            'Standard': {'Standard': 1.0, 'Premium': 0.7, 'Sugar-Free': 0.3},
            'Premium': {'Premium': 1.0, 'Standard': 0.7, 'Sugar-Free': 0.4},
            'Sugar-Free': {'Sugar-Free': 1.0, 'Standard': 0.3, 'Premium': 0.4}
        }
        
        # Technical parameters ranges from reference data
        self.technical_ranges = {}
        for param in ['Viscosity', 'pH', 'Fineness']:
            if param in self.classification_data.columns:
                self.technical_ranges[param] = {
                    'min': self.classification_data[param].min(),
                    'max': self.classification_data[param].max(),
                    'range': self.classification_data[param].max() - self.classification_data[param].min()
                }
    
    def find_matching_products(self, requirements: Dict) -> List[Dict]:
        """
        Find matching and similar products based on requirements
        
        Args:
            requirements: Dict containing product requirements
            
        Returns:
            List of matching products with their details and match scores
        """
        matches = []
        all_products = self.classification_data.copy()
        
        for _, product in all_products.iterrows():
            match_score, similarity_details = self._calculate_similarity_score(product, requirements)
            
            if match_score > 0.3:  # Include products with at least 30% similarity
                matches.append({
                    'material_code': product['Material_Code'],
                    'description': product['Material_Description'],
                    'match_score': match_score,
                    'similarity_details': similarity_details,
                    'details': self._get_product_details(product),
                    'is_exact_match': match_score > 0.8  # Consider products with >80% similarity as exact matches
                })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:10]  # Return top 10 matches
    
    def _calculate_similarity_score(self, product: pd.Series, requirements: Dict) -> Tuple[float, Dict]:
        """Calculate detailed similarity score between product and requirements"""
        scores = {}
        weights = {
            'base_type': 0.35,
            'product_type': 0.25,
            'technical_specs': 0.25,
            'region': 0.15
        }
        
        # Base type similarity
        if requirements.get('base_type'):
            req_base = requirements['base_type'].capitalize()
            prod_base = product['Base_Type'].split()[0].capitalize()  # Get primary base type
            base_similarity = self.base_type_similarity.get(req_base, {}).get(prod_base, 0.0)
            scores['base_type'] = base_similarity
        else:
            scores['base_type'] = 0.5  # Neutral score if no preference
        
        # Product type similarity
        if requirements.get('product_type'):
            req_type = requirements['product_type'].capitalize()
            prod_type = product['Product_Type'].split()[0].capitalize()
            type_similarity = self.product_type_similarity.get(req_type, {}).get(prod_type, 0.0)
            scores['product_type'] = type_similarity
        else:
            scores['product_type'] = 0.5
        
        # Technical specifications similarity
        if requirements.get('technical_specs'):
            tech_scores = []
            for param, value in requirements['technical_specs'].items():
                if param in product and param in self.technical_ranges:
                    range_info = self.technical_ranges[param]
                    normalized_diff = abs(float(product[param]) - float(value)) / range_info['range']
                    param_score = max(0, 1 - normalized_diff)
                    tech_scores.append(param_score)
            scores['technical_specs'] = sum(tech_scores) / len(tech_scores) if tech_scores else 0.5
        else:
            scores['technical_specs'] = 0.5
        
        # Region match
        if requirements.get('region'):
            scores['region'] = 1.0 if requirements['region'] == product['Region'] else 0.0
        else:
            scores['region'] = 0.5
        
        # Calculate weighted average
        total_score = sum(scores[key] * weights[key] for key in weights)
        
        return total_score, scores
    
    def _get_product_details(self, product: pd.Series) -> Dict:
        """Get detailed information about a product"""
        details = {
            'base_type': product['Base_Type'],
            'product_type': product['Product_Type'],
            'region': product['Region'],
            'technical_specs': {},
            'nutrition': self._get_nutrition_info(product['Material_Code']),
            'allergens': self._get_allergen_info(product['Material_Code'])
        }
        
        # Add technical specifications
        tech_columns = ['Viscosity', 'pH', 'Fineness', 'Shelf_Life']
        for col in tech_columns:
            if col in product:
                details['technical_specs'][col.lower()] = product[col]
        
        return details
    
    def _get_nutrition_info(self, material_code: str) -> Dict:
        """Get nutrition information for a product"""
        nutrition_row = self.nutrition_data[
            self.nutrition_data['Material_Code'] == material_code
        ].iloc[0] if len(self.nutrition_data) > 0 else None
        
        return nutrition_row.to_dict() if nutrition_row is not None else {}
    
    def _get_allergen_info(self, material_code: str) -> Dict:
        """Get allergen information for a product"""
        allergen_row = self.allergen_data[
            self.allergen_data['Material_Code'] == material_code
        ].iloc[0] if len(self.allergen_data) > 0 else None
        
        return allergen_row.to_dict() if allergen_row is not None else {}
