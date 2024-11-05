export interface AnalysisData {
  summary: string;
  requirements: {
    base_type?: string;
    product_type?: string;
    delivery_format?: string;
    technical_specs?: {
      [key: string]: number;
    };
    min_protein_percentage?: number;
    region?: string;
    special_requirements?: string;
  };
  product_matches: Array<{
    material_code: string;
    description: string;
    match_score: number;
    details: any;
    relaxation_details?: any;
    search_phase: string;
  }>;
  sales_pitch?: string;
  cross_sell_recommendations?: Array<{
    material_code: string;
    description: string;
    compatibility_score: number;
    compatibility_details: any;
    details: any;
    pairing_suggestions: string[];
  }>;
  cross_sell_pitch?: string;
}

export interface ApiError {
  error: string;
}
