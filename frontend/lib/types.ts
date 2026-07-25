/**
 * LeakLens — shared TypeScript types mirroring backend Pydantic models.
 */

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Transaction {
  id: string;
  merchant_raw: string;
  merchant_normalized: string;
  amount: number;
  currency: string;
  date: string;
  source_type: string;
}

export interface PriceHistoryEntry {
  amount: number;
  effective_date: string;
}

export interface ScoreComponents {
  unused: number;
  price_hike: number;
  redundancy: number;
  relative_cost: number;
}

export interface Subscription {
  id: string;
  merchant_normalized: string;
  category: string;
  category_display: string;
  frequency: string;
  first_seen: string;
  last_seen: string;
  current_amount: number;
  currency: string;
  status: string;
  leak_score: number | null;
  recommendation: string | null;
  reason: string | null;
  score_components: ScoreComponents | null;
  price_history: PriceHistoryEntry[];
  price_hike_detected: boolean;
  price_hike_pct: number | null;
  dark_pattern?: {
    has_dark_pattern: boolean;
    warning: string;
    escape_route: string[];
  };
  transactions?: Transaction[];
  actions?: ActionRecord[];
}

export interface SubscriptionListResponse {
  subscriptions: Subscription[];
  total: number;
}

export interface ActionRecord {
  id: string;
  subscription_id: string;
  action_taken: string;
  money_recovered: number;
  redirected_to_growth: boolean;
  created_at: string;
}

export interface ActionResponse extends ActionRecord {
  new_status: string;
  message: string;
}

export interface CategoryBreakdown {
  category: string;
  display_name: string;
  monthly_amount: number;
  count: number;
}

export interface DashboardSummary {
  total_monthly_spend: number;
  total_subscriptions: number;
  average_leak_score: number;
  potential_monthly_savings: number;
  total_recovered: number;
  category_breakdown: CategoryBreakdown[];
  recommendation_counts: {
    keep: number;
    downgrade: number;
    renegotiate: number;
    cancel: number;
  };
}

export interface GrowthProjection {
  years: number;
  total_contributed: number;
  projected_value: number;
  growth_amount: number;
}

export interface GrowthChartPoint {
  month: number;
  contributed: number;
  projected_value: number;
}

export interface GrowthSummary {
  total_monthly_contribution: number;
  total_recovered_to_date: number;
  actions_count: number;
  assumed_annual_return_pct: number;
  projections: GrowthProjection[];
  chart_data: GrowthChartPoint[];
  disclaimer: string;
}

export interface IngestResponse {
  transactions_parsed: number;
  subscriptions_detected: number;
  message: string;
}

export interface TransactionRecord {
  id: string;
  merchant_raw: string;
  merchant_normalized: string;
  amount: number;
  currency: string;
  date: string | null;
  source_type: string;
  category: string;
}

export interface TransactionListResponse {
  transactions: TransactionRecord[];
  total: number;
}

export interface NegotiateResponse {
  subscription_id: string;
  merchant: string;
  action: string;
  message: string;
  note: string;
}
