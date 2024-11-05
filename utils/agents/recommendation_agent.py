from typing import Dict, List, Optional
import pandas as pd

class RecommendationAgent:
    def __init__(self, classification_data: pd.DataFrame, nutrition_data: pd.DataFrame):
        self.classification_data = classification_data
        self.nutrition_data = nutrition_data
        
        # Base type similarity matrix
        self.base_type_similarity = {
            'Dark': {'Dark': 1.0, 'Milk': 0.3, 'White': 0.1, 'Ruby': 0.2},
            'Milk': {'Dark': 0.3, 'Milk': 1.0, 'White': 0.6, 'Ruby': 0.5},
            'White': {'Dark': 0.1, 'White': 1.0, 'Milk': 0.6, 'Ruby': 0.4},
            'Ruby': {'Dark': 0.2, 'Ruby': 1.0, 'Milk': 0.5, 'White': 0.4}
        }

    def get_recommendations(self, material_code: str) -> List[Dict]:
        """Generate cross-sell recommendations for a given product"""
        try:
            # Get the main product details
            main_product = self.classification_data[
                self.classification_data['Material_Code'] == material_code
            ].iloc[0]
            
            # Get potential complementary products
            recommendations = []
            base_type = main_product['Base_Type'].split()[0].capitalize()
            
            # Find complementary products with different base types
            complementary_products = self.classification_data[
                (self.classification_data['Material_Code'] != material_code) &
                (self.classification_data['Base_Type'].str.split().str[0] != base_type)
            ]
            
            for _, product in complementary_products.iterrows():
                compatibility_details = {
                    'base_type_match': self.base_type_similarity.get(base_type, {}).get(
                        product['Base_Type'].split()[0].capitalize(), 0.0
                    ),
                    'technical_compatibility': self._calculate_technical_compatibility(
                        main_product, product
                    ),
                    'regional_availability': 1.0 if product['Material_Code'][:2] == material_code[:2] else 0.5
                }
                
                # Calculate overall compatibility score
                compatibility_score = sum(compatibility_details.values()) / len(compatibility_details)
                
                if compatibility_score >= 0.6:  # Only include good matches
                    recommendations.append({
                        'material_code': product['Material_Code'],
                        'description': product['Material_Description'],
                        'compatibility_score': compatibility_score,
                        'compatibility_details': compatibility_details,
                        'details': self._get_product_details(product),
                        'pairing_suggestions': self._generate_pairing_suggestions(
                            main_product, product
                        )
                    })
            
            # Sort by compatibility score
            recommendations.sort(key=lambda x: x['compatibility_score'], reverse=True)
            return recommendations[:3]  # Return top 3 recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            return []

    def _calculate_technical_compatibility(self, product1: pd.Series, product2: pd.Series) -> float:
        """Calculate technical compatibility between two products"""
        try:
            # Compare viscosity ranges
            viscosity_diff = abs(float(product1['Viscosity']) - float(product2['Viscosity']))
            viscosity_score = max(0, 1 - (viscosity_diff / 0.5))  # Normalize difference
            
            # Compare pH values
            ph_diff = abs(float(product1['pH']) - float(product2['pH']))
            ph_score = max(0, 1 - (ph_diff / 0.5))
            
            return (viscosity_score + ph_score) / 2
        except:
            return 0.5  # Default score if comparison fails

    def _get_product_details(self, product: pd.Series) -> Dict:
        """Extract relevant product details"""
        return {
            'base_type': product['Base_Type'],
            'product_type': product['Product_Type'],
            'moulding_type': product['Moulding_Type'],
            'viscosity': float(product['Viscosity']),
            'ph': float(product['pH']),
            'fineness': float(product['Fineness']),
            'shelf_life': int(product['Shelf_Life']),
            'region_code': product['Material_Code'][:2]
        }

    def _generate_pairing_suggestions(self, main_product: pd.Series, complementary_product: pd.Series) -> List[str]:
        """Generate pairing suggestions for two products"""
        base1 = main_product['Base_Type'].split()[0].lower()
        base2 = complementary_product['Base_Type'].split()[0].lower()
        
        suggestions = [
            f"Create a layered effect by combining {base1} and {base2} chocolate",
            f"Use {base1} chocolate as base and {base2} chocolate for decoration",
            f"Blend both chocolates for a unique marble effect"
        ]
        return suggestions
