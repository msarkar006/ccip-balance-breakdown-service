/**
 * Balance breakdown types matching backend API responses
 */

export interface FreshnessInfo {
  level: string;
  as_of: string | null;
}

export interface SourceLink {
  source_type: string;
  source_id: number;
  source_reference: string;
}

export interface BalanceCategory {
  id: number;
  category_name: string;
  category_amount: string;
  apr: string;
  display_rank: number | null;
  promo_rate: string | null;
  promo_end_date: string | null;
  source_link: SourceLink | null;
}

export interface BalanceBreakdown {
  id: number;
  account_id: number;
  total_balance: string;
  pending_total: string;
  snapshot_date: string;
  categories: BalanceCategory[];
  freshness: FreshnessInfo;
  created_at: string;
  updated_at: string;
}

export interface BalanceBreakdownResponse {
  id: number;
  account_id: number;
  total_balance: string;
  pending_total: string;
  snapshot_date: string;
  categories: BalanceCategory[];
  freshness: FreshnessInfo;
  created_at: string;
  updated_at: string;
}
