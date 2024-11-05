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
        # Base type similarity matrix (for main matching)
        self.base_type_similarity = {
            'Dark': {'Dark': 1.0, 'Milk': 0.3, 'White': 0.1, 'Ruby': 0.2},
            'Milk': {'Dark': 0.3, 'Milk': 1.0, 'White': 0.6, 'Ruby': 0.5},
            'White': {'Dark': 0.1, 'White': 1.0, 'Milk': 0.6, 'Ruby': 0.4},
            'Ruby': {'Dark': 0.2, 'Ruby': 1.0, 'Milk': 0.5, 'White': 0.4}
        }
        
        # Base type complementarity matrix (for cross-selling)
        self.base_type_complementarity = {
            'Dark': {'Dark': 0.3, 'Milk': 0.9, 'White': 0.7, 'Ruby': 0.6},
            'Milk': {'Dark': 0.9, 'Milk': 0.4, 'White': 0.8, 'Ruby': 0.7},
            'White': {'Dark': 0.7, 'Milk': 0.8, 'White': 0.3, 'Ruby': 0.6},
            'Ruby': {'Dark': 0.6, 'Milk': 0.7, 'White': 0.6, 'Ruby': 0.3}
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
        """Find matching and similar products based on requirements"""
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
    
    def get_cross_sell_recommendations(self, material_code: str) -> List[Dict]:
        """
        Get cross-sell recommendations for a given product
        
        Args:
            material_code: Material code of the main product
            
        Returns:
            List of complementary products with compatibility scores
        """
        recommendations = []
        main_product = self.classification_data[
            self.classification_data['Material_Code'] == material_code
        ].iloc[0]
        
        all_products = self.classification_data[
            self.classification_data['Material_Code'] != material_code
        ]
        
        for _, product in all_products.iterrows():
            compatibility_score, compatibility_details = self._calculate_compatibility_score(
                main_product, product)
            
            if compatibility_score > 0.4:  # Include products with good compatibility
                recommendations.append({
                    'material_code': product['Material_Code'],
                    'description': product['Material_Description'],
                    'compatibility_score': compatibility_score,
                    'compatibility_details': compatibility_details,
                    'details': self._get_product_details(product),
                    'pairing_suggestions': self._generate_pairing_suggestions(
                        main_product, product)
                })
        
        # Sort by compatibility score
        recommendations.sort(key=lambda x: x['compatibility_score'], reverse=True)
        return recommendations[:5]  # Return top 5 recommendations
    
    def _calculate_compatibility_score(self, main_product: pd.Series, 
                                    complementary_product: pd.Series) -> Tuple[float, Dict]:
        """Calculate compatibility score between two products"""
        scores = {}
        weights = {
            'base_type_complement': 0.35,
            'product_type_match': 0.25,
            'technical_compatibility': 0.25,
            'region_availability': 0.15
        }
        
        # Base type complementarity
        main_base = main_product['Base_Type'].split()[0].capitalize()
        comp_base = complementary_product['Base_Type'].split()[0].capitalize()
        scores['base_type_complement'] = self.base_type_complementarity.get(
            main_base, {}).get(comp_base, 0.0)
        
        # Product type matching (premium with premium, etc.)
        main_type = main_product['Product_Type'].split()[0].capitalize()
        comp_type = complementary_product['Product_Type'].split()[0].capitalize()
        scores['product_type_match'] = self.product_type_similarity.get(
            main_type, {}).get(comp_type, 0.0)
        
        # Technical compatibility
        tech_scores = []
        for param in ['Viscosity', 'pH']:
            if param in main_product and param in complementary_product:
                diff = abs(float(main_product[param]) - float(complementary_product[param]))
                range_info = self.technical_ranges[param]
                normalized_diff = diff / range_info['range']
                tech_scores.append(max(0, 1 - normalized_diff))
        scores['technical_compatibility'] = sum(tech_scores) / len(tech_scores) if tech_scores else 0.5
        
        # Region availability (same region preferred)
        scores['region_availability'] = 1.0 if main_product['Region'] == complementary_product['Region'] else 0.5
        
        # Calculate weighted average
        total_score = sum(scores[key] * weights[key] for key in weights)
        
        return total_score, scores
    
    def _generate_pairing_suggestions(self, main_product: pd.Series, 
                                    complementary_product: pd.Series) -> List[str]:
        """Generate pairing suggestions for two products"""
        suggestions = []
        
        # Base type combinations
        main_base = main_product['Base_Type'].split()[0].lower()
        comp_base = complementary_product['Base_Type'].split()[0].lower()
        
        if main_base == 'dark' and comp_base == 'milk':
            suggestions.append("Create a luxurious layered dessert")
            suggestions.append("Perfect for dual-flavor molding")
        elif main_base == 'dark' and comp_base == 'white':
            suggestions.append("Ideal for striking visual contrast in decorative pieces")
            suggestions.append("Excellent for marbled effects")
        elif main_base == 'milk' and comp_base == 'white':
            suggestions.append("Great for creamy, multi-layered confections")
            suggestions.append("Perfect for swirled presentations")
        
        # Product type combinations
        if 'premium' in main_product['Product_Type'].lower():
            suggestions.append("Combine for luxury gift assortments")
        if 'sugar-free' in main_product['Product_Type'].lower():
            suggestions.append("Ideal for health-conscious variety packs")
        
        return suggestions if suggestions else ["Versatile combination for various applications"]
    
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
            prod_base = product['Base_Type'].split()[0].capitalize()
            base_similarity = self.base_type_similarity.get(req_base, {}).get(prod_base, 0.0)
            scores['base_type'] = base_similarity
        else:
            scores['base_type'] = 0.5
        
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
