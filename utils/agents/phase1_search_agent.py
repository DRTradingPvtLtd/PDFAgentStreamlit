from typing import Dict, List, Tuple
import pandas as pd

class Phase1SearchAgent:
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

    def search(self, requirements: Dict) -> Tuple[List[Dict], Dict]:
        """
        Perform Phase 1 search with strict criteria
        Returns: (matching_products, search_stats)
        """
        products = self.classification_data.copy()
        initial_count = len(products)
        stats = {'initial_count': initial_count}
        
        # Apply strict filters
        if requirements.get('base_type'):
            products = products[products['Base_Type'].str.contains(requirements['base_type'], case=False)]
            stats['after_base_type'] = len(products)

        if requirements.get('product_type'):
            products = products[products['Product_Type'].str.contains(requirements['product_type'], case=False)]
            stats['after_product_type'] = len(products)

        if requirements.get('delivery_format'):
            products = products[products['Moulding_Type'].str.contains(requirements['delivery_format'], case=False)]
            stats['after_delivery_format'] = len(products)

        # Technical specifications
        if requirements.get('technical_specs'):
            for spec, value in requirements['technical_specs'].items():
                if spec in products.columns:
                    products = products[
                        (products[spec] >= float(value) * 0.95) &  # Allow 5% tolerance
                        (products[spec] <= float(value) * 1.05)
                    ]
            stats['after_technical_specs'] = len(products)

        # Protein content
        if requirements.get('min_protein_percentage'):
            protein_threshold = float(requirements['min_protein_percentage'])
            products = pd.merge(
                products,
                self.nutrition_data[['Material_Code', 'Protein_g']],
                on='Material_Code',
                how='left'
            )
            products = products[products['Protein_g'] >= protein_threshold]
            stats['after_protein_filter'] = len(products)

        # Convert matches to list of dictionaries
        matches = []
        for _, product in products.iterrows():
            match_details = self._get_product_details(product)
            match_score = self._calculate_match_score(product, requirements)
            
            matches.append({
                'material_code': product['Material_Code'],
                'description': product['Material_Description'],
                'match_score': match_score,
                'details': match_details,
                'search_phase': 'Phase 1 (Strict)'
            })

        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        stats['final_count'] = len(matches)
        
        return matches, stats

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

    def _calculate_match_score(self, product: pd.Series, requirements: Dict) -> float:
        """Calculate how well a product matches the requirements"""
        scores = []
        weights = {
            'base_type': 0.3,
            'delivery_format': 0.2,
            'technical_specs': 0.3,
            'protein_content': 0.2
        }

        # Base type match
        if requirements.get('base_type'):
            req_base = requirements['base_type'].capitalize()
            prod_base = product['Base_Type'].split()[0].capitalize()
            base_score = self.base_type_similarity.get(req_base, {}).get(prod_base, 0.0)
            scores.append(('base_type', base_score))

        # Delivery format match
        if requirements.get('delivery_format'):
            req_format = requirements['delivery_format'].lower()
            prod_format = product['Moulding_Type'].lower()
            format_score = 1.0 if req_format in prod_format else 0.0
            scores.append(('delivery_format', format_score))

        # Technical specifications match
        if requirements.get('technical_specs'):
            tech_scores = []
            for spec, value in requirements['technical_specs'].items():
                if spec in product:
                    diff = abs(float(product[spec]) - float(value))
                    tolerance = float(value) * 0.05  # 5% tolerance
                    tech_score = max(0, 1 - (diff / tolerance))
                    tech_scores.append(tech_score)
            if tech_scores:
                scores.append(('technical_specs', sum(tech_scores) / len(tech_scores)))

        # Calculate weighted average
        if scores:
            total_weight = sum(weights[category] for category, _ in scores)
            weighted_score = sum(weights[category] * score for category, score in scores) / total_weight
            return weighted_score
        return 0.0
