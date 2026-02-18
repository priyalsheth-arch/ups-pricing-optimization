export interface Store {
  id: number
  name: string
  store_number: string
  address: string | null
  city: string | null
  state: string | null
  created_at: string
}

export interface User {
  id: number
  email: string
  full_name: string | null
  role: 'admin' | 'manager' | 'staff'
  store_id: number | null
}

export interface AuthState {
  token: string | null
  role: string | null
  store_id: number | null
  full_name: string | null
}

export interface UploadBatch {
  id: number
  store_id: number
  filename: string
  row_count: number | null
  status: 'pending' | 'processing' | 'complete' | 'error'
  error_message: string | null
  date_range_start: string | null
  date_range_end: string | null
  uploaded_at: string
}

export interface UploadPreviewRow {
  row_number: number
  transaction_date: string | null
  service_category: string | null
  service_code: string | null
  service_description: string | null
  quantity: number | null
  net_revenue: number | null
  carrier: string | null
  service_level: string | null
  raw_data: Record<string, string>
}

export interface ValidationReport {
  total_rows: number
  valid_rows: number
  error_rows: number
  warnings: string[]
  errors: string[]
  date_range_start: string | null
  date_range_end: string | null
}

export interface OurPrice {
  id: number
  store_id: number
  service_code: string
  service_category: string
  service_name: string
  unit: string | null
  price: string
  effective_date: string
  notes: string | null
  updated_at: string
}

export interface CompetitorPrice {
  id: number
  competitor_name: string
  service_code: string
  service_category: string
  service_name: string
  unit: string | null
  price: string
  effective_date: string
  source_notes: string | null
  updated_at: string
}

export interface PricingGap {
  id: number
  store_id: number
  service_code: string
  service_category: string
  service_name: string | null
  our_price: string | null
  competitor_name: string
  competitor_price: string | null
  gap_amount: string | null
  gap_pct: string | null
  direction: 'underpriced' | 'overpriced' | 'competitive' | null
  transaction_volume: number | null
  revenue_impact: string | null
  analysis_date: string
  period_start: string | null
  period_end: string | null
}

export interface UpsellOpportunity {
  id: number
  store_id: number
  rule_id: string
  opportunity_type: string
  trigger_service: string
  trigger_category: string
  recommended_service: string
  recommended_service_code: string
  price_delta: string | null
  conversion_rate_est: string | null
  monthly_volume: number | null
  monthly_impact_est: string | null
  priority: 'high' | 'medium' | 'low' | null
  staff_script: string | null
  is_dismissed: boolean
  analysis_date: string
}

export interface CategoryOpportunity {
  category: string
  pricing_gap_opportunity: string
  upsell_opportunity: string
  addon_opportunity: string
  total: string
}

export interface RevenueOpportunityReport {
  store_id: number
  period_start: string
  period_end: string
  current_period_revenue: string
  prior_period_revenue: string
  pricing_gap_opportunity: string
  upsell_opportunity: string
  addon_opportunity: string
  total_monthly_opportunity: string
  annual_opportunity: string
  by_category: CategoryOpportunity[]
  assumptions: {
    price_elasticity_factor: number
    ground_to_2day_conversion: number
    ground_to_3day_conversion: number
    insurance_attach_rate: number
    packing_supplies_attach: number
    printing_finishing_attach: number
    max_price_increase_pct: number
    analysis_period_months: number
  }
}

export interface DashboardSummary {
  store_id: number
  period_days: number
  period_start: string
  period_end: string
  total_revenue: string
  revenue_vs_prior_period: string | null
  transactions_analyzed: number
  top_gaps: PricingGap[]
  top_upsells: UpsellOpportunity[]
  total_opportunity_est: string
  last_upload_date: string | null
  underpriced_services: number
  high_priority_upsells: number
}

export interface MultiStoreComparison {
  store_id: number
  store_name: string
  store_number: string
  current_revenue: string
  total_opportunity: string
  top_gap_service: string | null
  top_gap_amount: string | null
  top_upsell_service: string | null
  top_upsell_impact: string | null
  underpriced_service_count: number
}
