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
        
        # Market segments and their applications
        self.market_segments = {
            'Confectionery': ['Tablets', 'Pralines', 'Countlines', 'Protein Bars'],
            'Bakery': ['Butter cakes', 'Celebration cakes', 'Laminated pastries'],
            'Ice Cream': ['Ice cream bars', 'Ice cream cones', 'Ice cream sandwiches'],
            'Desserts': ['Frozen desserts', 'Spoonable desserts', 'Yogurt applications']
        }
        
        # Delivery format alternatives
        self.delivery_format_alternatives = {
            'Drops': ['Block', 'Callets', 'Easymelt'],
            'Block': ['Drops', 'Callets', 'Easymelt'],
            'Callets': ['Drops', 'Block', 'Easymelt'],
            'Easymelt': ['Drops', 'Block', 'Callets']
        }
        
        # Region mappings
        self.region_mappings = {
            'EU': ['BE', 'NL', 'PL', 'TR'],  # Belgium, Netherlands, Poland, Turkey
            'NAM': ['US', 'CA'],  # USA, Canada
            'APAC': ['SG', 'JP', 'AU']  # Singapore, Japan, Australia
        }
    
    def phase1_search(self, requirements: Dict) -> Tuple[List[Dict], Dict]:
        """
        Perform Phase 1 search with strict criteria
        Returns: (matching_products, search_stats)
        """
        products = self.classification_data.copy()
        initial_count = len(products)
        stats = {'initial_count': initial_count}
        
        # 1. Market Segment & Application Filter
        if requirements.get('market_segment'):
            segment = requirements['market_segment'].lower()
            applications = self.market_segments.get(segment.capitalize(), [])
            if applications:
                products = products[products['Category'].str.lower().isin([app.lower() for app in applications])]
                stats['after_segment_filter'] = len(products)
        
        # 2. Product Type Filter
        if requirements.get('product_type'):
            products = products[products['Product_Type'].str.contains(requirements['product_type'], case=False)]
            stats['after_product_type'] = len(products)
        
        # 3. Base Type Filter
        if requirements.get('base_type'):
            products = products[products['Base_Type'].str.contains(requirements['base_type'], case=False)]
            stats['after_base_type'] = len(products)
        
        # 4. Delivery Format Filter
        if requirements.get('delivery_format'):
            products = products[products['Moulding_Type'].str.contains(requirements['delivery_format'], case=False)]
            stats['after_delivery_format'] = len(products)
        
        # 5. Technical Requirements
        if requirements.get('technical_specs'):
            for spec, value in requirements['technical_specs'].items():
                if spec in products.columns:
                    products = products[
                        (products[spec] >= float(value) * 0.9) & 
                        (products[spec] <= float(value) * 1.1)
                    ]
            stats['after_technical_specs'] = len(products)
        
        # 6. Protein Content Filter
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
        
        # Convert remaining products to list of dictionaries
        matches = []
        for _, product in products.iterrows():
            match_details = self._get_product_details(product)
            match_score = self._calculate_match_score(product, requirements)
            matches.append({
                'material_code': product['Material_Code'],
                'description': product['Material_Description'],
                'match_score': match_score,
                'details': match_details
            })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        stats['final_count'] = len(matches)
        
        return matches, stats

    def phase2_search(self, requirements: Dict) -> Tuple[List[Dict], Dict]:
        """
        Perform Phase 2 search with relaxed criteria
        Returns: (matching_products, search_stats)
        """
        relaxed_requirements = requirements.copy()
        stats = {'original_requirements': requirements}
        
        # 1. Relax delivery format requirements
        if requirements.get('delivery_format'):
            original_format = requirements['delivery_format']
            alternative_formats = self.delivery_format_alternatives.get(original_format, [])
            relaxed_requirements['delivery_format'] = '|'.join([original_format] + alternative_formats)
        
        # 2. Relax protein percentage requirement
        if requirements.get('min_protein_percentage'):
            original_protein = float(requirements['min_protein_percentage'])
            relaxed_protein = original_protein * 0.8  # 20% relaxation
            relaxed_requirements['min_protein_percentage'] = relaxed_protein
            stats['relaxed_protein_requirement'] = relaxed_protein
        
        # 3. Expand regional search
        if requirements.get('region'):
            original_region = requirements['region']
            region_codes = self.region_mappings.get(original_region, [])
            if region_codes:
                relaxed_requirements['region_codes'] = region_codes
        
        # Perform search with relaxed requirements
        products = self.classification_data.copy()
        initial_count = len(products)
        stats['initial_count'] = initial_count
        
        # Apply relaxed filters
        # 1. Market Segment & Application (keep original)
        if relaxed_requirements.get('market_segment'):
            segment = relaxed_requirements['market_segment'].lower()
            applications = self.market_segments.get(segment.capitalize(), [])
            if applications:
                products = products[products['Category'].str.lower().isin([app.lower() for app in applications])]
                stats['after_segment_filter'] = len(products)
        
        # 2. Base Type (keep original)
        if relaxed_requirements.get('base_type'):
            products = products[products['Base_Type'].str.contains(relaxed_requirements['base_type'], case=False)]
            stats['after_base_type'] = len(products)
        
        # 3. Apply relaxed delivery format
        if relaxed_requirements.get('delivery_format'):
            products = products[products['Moulding_Type'].str.contains(relaxed_requirements['delivery_format'], case=False)]
            stats['after_delivery_format'] = len(products)
        
        # 4. Apply relaxed protein requirement
        if relaxed_requirements.get('min_protein_percentage'):
            protein_threshold = float(relaxed_requirements['min_protein_percentage'])
            products = pd.merge(
                products,
                self.nutrition_data[['Material_Code', 'Protein_g']],
                on='Material_Code',
                how='left'
            )
            products = products[products['Protein_g'] >= protein_threshold]
            stats['after_protein_filter'] = len(products)
        
        # 5. Apply regional filter
        if relaxed_requirements.get('region_codes'):
            products = products[products['Material_Code'].str[:2].isin(relaxed_requirements['region_codes'])]
            stats['after_region_filter'] = len(products)
        
        # Convert remaining products to list of dictionaries with additional information
        matches = []
        for _, product in products.iterrows():
            match_details = self._get_product_details(product)
            match_score = self._calculate_match_score(product, requirements)  # Use original requirements for scoring
            relaxation_details = self._calculate_relaxation_details(product, requirements, relaxed_requirements)
            
            matches.append({
                'material_code': product['Material_Code'],
                'description': product['Material_Description'],
                'match_score': match_score,
                'details': match_details,
                'relaxation_details': relaxation_details
            })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        stats['final_count'] = len(matches)
        
        return matches, stats

    def _calculate_match_score(self, product: pd.Series, requirements: Dict) -> float:
        """Calculate how well a product matches the original requirements"""
        scores = []
        weights = {
            'base_type': 0.3,
            'delivery_format': 0.2,
            'protein_content': 0.3,
            'region': 0.2
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
            format_score = 1.0 if req_format in prod_format else 0.5 if req_format in self.delivery_format_alternatives else 0.0
            scores.append(('delivery_format', format_score))
        
        # Protein content match
        if requirements.get('min_protein_percentage'):
            req_protein = float(requirements['min_protein_percentage'])
            prod_protein = float(self.nutrition_data[
                self.nutrition_data['Material_Code'] == product['Material_Code']
            ]['Protein_g'].iloc[0])
            protein_score = min(prod_protein / req_protein, 1.0) if prod_protein >= req_protein * 0.8 else 0.0
            scores.append(('protein_content', protein_score))
        
        # Region match
        if requirements.get('region'):
            req_region = requirements['region']
            prod_region_code = product['Material_Code'][:2]
            region_score = 1.0 if prod_region_code in self.region_mappings.get(req_region, []) else 0.0
            scores.append(('region', region_score))
        
        # Calculate weighted average
        if scores:
            weighted_score = sum(weights[category] * score for category, score in scores)
            return weighted_score
        return 0.0

    def _calculate_relaxation_details(self, product: pd.Series, original_reqs: Dict, relaxed_reqs: Dict) -> Dict:
        """Calculate and explain how requirements were relaxed for this match"""
        relaxations = {}
        
        # Check delivery format relaxation
        if original_reqs.get('delivery_format') != relaxed_reqs.get('delivery_format'):
            original_format = original_reqs['delivery_format']
            current_format = product['Moulding_Type']
            relaxations['delivery_format'] = {
                'original': original_format,
                'current': current_format,
                'notes': f"Alternative format accepted: {current_format}"
            }
        
        # Check protein content relaxation
        if original_reqs.get('min_protein_percentage') != relaxed_reqs.get('min_protein_percentage'):
            original_protein = float(original_reqs['min_protein_percentage'])
            current_protein = float(self.nutrition_data[
                self.nutrition_data['Material_Code'] == product['Material_Code']
            ]['Protein_g'].iloc[0])
            protein_difference = ((original_protein - current_protein) / original_protein) * 100
            relaxations['protein_content'] = {
                'original': f"{original_protein}%",
                'current': f"{current_protein}%",
                'difference': f"{protein_difference:.1f}% lower than requested"
            }
        
        # Check region relaxation
        if original_reqs.get('region') and 'region_codes' in relaxed_reqs:
            original_region = original_reqs['region']
            current_region_code = product['Material_Code'][:2]
            relaxations['region'] = {
                'original': original_region,
                'current': current_region_code,
                'notes': "Alternative production location accepted"
            }
        
        return relaxations

    def _get_product_details(self, product: pd.Series) -> Dict:
        """Get comprehensive product details including nutrition and allergen information"""
        details = {
            'base_type': product['Base_Type'],
            'product_type': product['Product_Type'],
            'moulding_type': product['Moulding_Type'],
            'technical_specs': {},
            'nutrition': self._get_nutrition_info(product['Material_Code']),
            'allergens': self._get_allergen_info(product['Material_Code']),
            'production_location': product['Material_Code'][:2]
        }
        
        # Add technical specifications
        for col in ['Viscosity', 'pH', 'Fineness', 'Shelf_Life']:
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

    def find_matching_products(self, requirements: Dict) -> List[Dict]:
        """
        Main entry point for product matching. Implements two-phase search strategy.
        """
        # Phase 1: Strict search
        phase1_matches, phase1_stats = self.phase1_search(requirements)
        
        # If Phase 1 yields sufficient results, return them
        if len(phase1_matches) >= 5:
            return phase1_matches
        
        # Phase 2: Relaxed search
        phase2_matches, phase2_stats = self.phase2_search(requirements)
        
        # Combine unique matches from both phases
        all_matches = phase1_matches.copy()
        existing_codes = {match['material_code'] for match in all_matches}
        
        for match in phase2_matches:
            if match['material_code'] not in existing_codes:
                match['phase'] = 'phase2'  # Mark as Phase 2 match
                all_matches.append(match)
                existing_codes.add(match['material_code'])
        
        # Sort combined results by match score
        all_matches.sort(key=lambda x: x['match_score'], reverse=True)
        return all_matches[:10]  # Return top 10 matches
