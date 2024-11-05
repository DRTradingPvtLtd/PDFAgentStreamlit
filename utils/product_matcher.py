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
        
        # Initialize mappings
        self._init_mappings()
    
    def _init_mappings(self):
        """Initialize internal mappings for quick lookups"""
        self.base_type_mapping = {}
        self.product_type_mapping = {}
        self.viscosity_ranges = {}
        
        # Create mappings from technical parameters
        for _, row in self.technical_params.iterrows():
            technique = row['Technique']
            segment = row['Segment']
            key = f"{technique}_{segment}"
            self.viscosity_ranges[key] = {
                'min_viscosity': row['Min Viscosity (Casson)'],
                'max_viscosity': row['Max Viscosity (Casson)']
            }
    
    def find_matching_products(self, 
                             requirements: Dict,
                             user_preferences: Optional[Dict] = None) -> List[Dict]:
        """
        Find matching products based on requirements and user preferences
        
        Args:
            requirements: Dict containing product requirements
            user_preferences: Optional dict containing user chocolate preferences
            
        Returns:
            List of matching products with their details and match scores
        """
        matches = []
        filtered_products = self._apply_initial_filters(requirements)
        
        for _, product in filtered_products.iterrows():
            match_score = self._calculate_match_score(product, requirements, user_preferences)
            if match_score > 0.5:  # Minimum threshold for considering a match
                matches.append({
                    'material_code': product['Material_Code'],
                    'description': product['Material_Description'],
                    'match_score': match_score,
                    'details': self._get_product_details(product)
                })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:5]  # Return top 5 matches
    
    def _apply_initial_filters(self, requirements: Dict) -> pd.DataFrame:
        """Apply initial filters based on basic requirements"""
        filtered = self.classification_data.copy()
        
        # Apply base filters
        if 'base_type' in requirements:
            filtered = filtered[filtered['Base_Type'].str.contains(
                requirements['base_type'], case=False, na=False)]
            
        if 'product_type' in requirements:
            filtered = filtered[filtered['Product_Type'].str.contains(
                requirements['product_type'], case=False, na=False)]
            
        if 'region' in requirements:
            filtered = filtered[filtered['Region'] == requirements['region']]
            
        return filtered
    
    def _calculate_match_score(self, 
                             product: pd.Series, 
                             requirements: Dict,
                             user_preferences: Optional[Dict]) -> float:
        """Calculate match score between product and requirements"""
        score = 0.0
        weights = {
            'base_type': 0.3,
            'product_type': 0.2,
            'technical_params': 0.3,
            'user_preferences': 0.2
        }
        
        # Base type match
        if requirements.get('base_type'):
            if requirements['base_type'].lower() in product['Base_Type'].lower():
                score += weights['base_type']
        
        # Product type match
        if requirements.get('product_type'):
            if requirements['product_type'].lower() in product['Product_Type'].lower():
                score += weights['product_type']
        
        # Technical parameters match
        if requirements.get('technical_params'):
            tech_score = self._check_technical_parameters(
                product, requirements['technical_params'])
            score += tech_score * weights['technical_params']
        
        # User preferences match
        if user_preferences:
            pref_score = self._check_user_preferences(product, user_preferences)
            score += pref_score * weights['user_preferences']
        
        return score
    
    def _check_technical_parameters(self, 
                                  product: pd.Series, 
                                  tech_params: Dict) -> float:
        """Check if product meets technical parameters"""
        score = 0.0
        total_params = len(tech_params)
        
        for param, value in tech_params.items():
            if param in product and self._is_within_range(product[param], value):
                score += 1.0
        
        return score / total_params if total_params > 0 else 0.0
    
    def _check_user_preferences(self, 
                              product: pd.Series, 
                              preferences: Dict) -> float:
        """Check how well product matches user preferences"""
        score = 0.0
        total_prefs = len(preferences)
        
        # Check chocolate type preference
        if preferences.get('chocolate_type'):
            if preferences['chocolate_type'].lower() in product['Base_Type'].lower():
                score += 1.0
        
        # Check dietary restrictions
        if preferences.get('dietary_restrictions'):
            allergen_info = self._get_allergen_info(product['Material_Code'])
            if self._meets_dietary_restrictions(allergen_info, 
                                             preferences['dietary_restrictions']):
                score += 1.0
        
        # Check cocoa percentage
        if preferences.get('cocoa_percentage'):
            if self._matches_cocoa_percentage(product, preferences['cocoa_percentage']):
                score += 1.0
        
        return score / total_prefs if total_prefs > 0 else 0.0
    
    def _get_allergen_info(self, material_code: str) -> Dict:
        """Get allergen information for a product"""
        allergen_row = self.allergen_data[
            self.allergen_data['Material_Code'] == material_code
        ].iloc[0] if len(self.allergen_data) > 0 else None
        
        return allergen_row.to_dict() if allergen_row is not None else {}
    
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
    
    @staticmethod
    def _is_within_range(value: float, target: Union[float, Tuple[float, float]]) -> bool:
        """Check if value is within acceptable range"""
        if isinstance(target, tuple):
            return target[0] <= value <= target[1]
        return abs(value - target) / target <= 0.1  # 10% tolerance
    
    @staticmethod
    def _meets_dietary_restrictions(allergen_info: Dict, 
                                  restrictions: List[str]) -> bool:
        """Check if product meets dietary restrictions"""
        for restriction in restrictions:
            if restriction.lower() == 'vegan':
                if not allergen_info.get('Suitable_For_Vegans', False):
                    return False
            elif restriction.lower() == 'gluten-free':
                if allergen_info.get('Contains_Gluten', False):
                    return False
            # Add more restriction checks as needed
        return True
    
    @staticmethod
    def _matches_cocoa_percentage(product: pd.Series, 
                                target_percentage: int) -> bool:
        """Check if product matches desired cocoa percentage"""
        # This is a simplified check - would need actual cocoa percentage data
        if 'cocoa_percentage' in product:
            return abs(product['cocoa_percentage'] - target_percentage) <= 5
        return False
