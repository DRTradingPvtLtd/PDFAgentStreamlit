from typing import Dict, List, Tuple
import pandas as pd

class Phase2SearchAgent:
    def __init__(self, classification_data: pd.DataFrame, nutrition_data: pd.DataFrame):
        self.classification_data = classification_data
        self.nutrition_data = nutrition_data
        
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

    @staticmethod
    def clean_percentage(value: str) -> float:
        """Convert a percentage string to float, removing the % symbol"""
        return float(str(value).replace('%', '').strip())

    def _relax_requirements(self, requirements: Dict) -> Dict:
        """Relax the search criteria"""
        relaxed = requirements.copy()
        
        # Relax delivery format
        if requirements.get('delivery_format'):
            original_format = requirements['delivery_format']
            alternatives = self.delivery_format_alternatives.get(original_format, [])
            relaxed['delivery_format'] = '|'.join([original_format] + alternatives)
        
        # Relax protein requirement
        if requirements.get('min_protein_percentage'):
            try:
                protein_value = (
                    float(requirements['min_protein_percentage'])
                    if not isinstance(requirements['min_protein_percentage'], str)
                    else self.clean_percentage(requirements['min_protein_percentage'])
                )
                relaxed['min_protein_percentage'] = protein_value * 0.8  # 20% relaxation
            except (ValueError, TypeError):
                pass
        
        # Relax technical specifications
        if requirements.get('technical_specs'):
            relaxed_specs = {}
            for spec, value in requirements['technical_specs'].items():
                try:
                    target_value = float(value) if not isinstance(value, str) else self.clean_percentage(value)
                    relaxed_specs[spec] = {
                        'min': target_value * 0.8,  # 20% lower
                        'max': target_value * 1.2   # 20% higher
                    }
                except (ValueError, TypeError):
                    continue
            relaxed['technical_specs'] = relaxed_specs
        
        return relaxed

    def _apply_filters(self, products: pd.DataFrame, requirements: Dict) -> pd.DataFrame:
        """Apply relaxed filters to the product dataset"""
        filtered = products.copy()
        
        # Base type filter (keep original)
        if requirements.get('base_type'):
            filtered = filtered[filtered['Base_Type'].str.contains(requirements['base_type'], case=False)]
        
        # Relaxed delivery format
        if requirements.get('delivery_format'):
            filtered = filtered[filtered['Moulding_Type'].str.contains(requirements['delivery_format'], case=False)]
        
        # Relaxed technical specifications
        if requirements.get('technical_specs'):
            for spec, range_values in requirements['technical_specs'].items():
                if spec in filtered.columns:
                    filtered = filtered[
                        (filtered[spec] >= range_values['min']) &
                        (filtered[spec] <= range_values['max'])
                    ]
        
        # Relaxed protein requirement
        if requirements.get('min_protein_percentage'):
            try:
                protein_threshold = (
                    float(requirements['min_protein_percentage'])
                    if not isinstance(requirements['min_protein_percentage'], str)
                    else self.clean_percentage(requirements['min_protein_percentage'])
                )
                filtered = pd.merge(
                    filtered,
                    self.nutrition_data[['Material_Code', 'Protein_g']],
                    on='Material_Code',
                    how='left'
                )
                filtered = filtered[filtered['Protein_g'] >= protein_threshold]
            except (ValueError, TypeError):
                pass
        
        return filtered

    def search(self, requirements: Dict) -> Tuple[List[Dict], Dict]:
        """
        Perform Phase 2 search with relaxed criteria
        Returns: (matching_products, search_stats)
        """
        relaxed_requirements = self._relax_requirements(requirements)
        stats = {
            'original_requirements': requirements,
            'relaxed_requirements': relaxed_requirements
        }
        
        products = self.classification_data.copy()
        initial_count = len(products)
        stats['initial_count'] = initial_count

        # Apply relaxed filters
        products = self._apply_filters(products, relaxed_requirements)
        
        # Convert matches to list of dictionaries
        matches = []
        for _, product in products.iterrows():
            match_details = self._get_product_details(product)
            match_score = self._calculate_match_score(product, requirements)  # Score against original requirements
            relaxation_details = self._calculate_relaxation_details(
                product, requirements, relaxed_requirements)
            
            matches.append({
                'material_code': product['Material_Code'],
                'description': product['Material_Description'],
                'match_score': match_score,
                'details': match_details,
                'relaxation_details': relaxation_details,
                'search_phase': 'Phase 2 (Relaxed)'
            })

        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        stats['final_count'] = len(matches)
        
        return matches, stats

    def _calculate_relaxation_details(self, product: pd.Series, original_reqs: Dict, relaxed_reqs: Dict) -> Dict:
        """Calculate how requirements were relaxed for this match"""
        relaxations = {}
        
        # Check delivery format relaxation
        if original_reqs.get('delivery_format') != relaxed_reqs.get('delivery_format'):
            original_format = original_reqs['delivery_format']
            product_format = product['Moulding_Type']
            if original_format.lower() not in product_format.lower():
                relaxations['delivery_format'] = {
                    'original': original_format,
                    'accepted': product_format,
                    'relaxation_level': 'Alternative format accepted'
                }
        
        # Check protein content relaxation
        if original_reqs.get('min_protein_percentage'):
            try:
                original_protein = (
                    float(original_reqs['min_protein_percentage'])
                    if not isinstance(original_reqs['min_protein_percentage'], str)
                    else self.clean_percentage(original_reqs['min_protein_percentage'])
                )
                product_protein = float(self.nutrition_data[
                    self.nutrition_data['Material_Code'] == product['Material_Code']
                ]['Protein_g'].iloc[0])
                
                if product_protein < original_protein:
                    relaxations['protein_content'] = {
                        'original': original_protein,
                        'accepted': product_protein,
                        'relaxation_percentage': ((original_protein - product_protein) / original_protein) * 100
                    }
            except (ValueError, TypeError, IndexError):
                pass
        
        # Check technical specifications relaxation
        if original_reqs.get('technical_specs'):
            tech_relaxations = {}
            for spec, value in original_reqs['technical_specs'].items():
                if spec in product:
                    try:
                        original_value = float(value) if not isinstance(value, str) else self.clean_percentage(value)
                        product_value = float(product[spec])
                        diff_percentage = abs((product_value - original_value) / original_value) * 100
                        
                        if diff_percentage > 5:  # More than 5% difference
                            tech_relaxations[spec] = {
                                'original': original_value,
                                'accepted': product_value,
                                'difference_percentage': diff_percentage
                            }
                    except (ValueError, TypeError):
                        continue
            
            if tech_relaxations:
                relaxations['technical_specs'] = tech_relaxations
        
        return relaxations

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

    def _calculate_match_score(self, product: pd.Series, original_requirements: Dict) -> float:
        """Calculate match score against original requirements"""
        scores = []
        weights = {
            'base_type': 0.3,
            'delivery_format': 0.2,
            'technical_specs': 0.3,
            'protein_content': 0.2
        }

        # Base type match (strict)
        if original_requirements.get('base_type'):
            base_score = 1.0 if original_requirements['base_type'].lower() in product['Base_Type'].lower() else 0.0
            scores.append(('base_type', base_score))

        # Delivery format match (relaxed)
        if original_requirements.get('delivery_format'):
            req_format = original_requirements['delivery_format'].lower()
            prod_format = product['Moulding_Type'].lower()
            format_score = 1.0 if req_format in prod_format else \
                          0.7 if req_format in self.delivery_format_alternatives else \
                          0.0
            scores.append(('delivery_format', format_score))

        # Technical specifications match (relaxed)
        if original_requirements.get('technical_specs'):
            tech_scores = []
            for spec, value in original_requirements['technical_specs'].items():
                if spec in product:
                    try:
                        target_value = float(value) if not isinstance(value, str) else self.clean_percentage(value)
                        actual_value = float(product[spec])
                        diff = abs(actual_value - target_value)
                        tolerance = target_value * 0.2  # 20% tolerance
                        tech_score = max(0, 1 - (diff / tolerance))
                        tech_scores.append(tech_score)
                    except (ValueError, TypeError):
                        continue
            if tech_scores:
                scores.append(('technical_specs', sum(tech_scores) / len(tech_scores)))

        # Calculate weighted average
        if scores:
            total_weight = sum(weights[category] for category, _ in scores)
            weighted_score = sum(weights[category] * score for category, score in scores) / total_weight
            return weighted_score
        return 0.0
