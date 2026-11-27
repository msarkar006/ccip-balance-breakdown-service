/**
 * Transaction types matching backend API responses
 */

export interface FreshnessInfo {
  level: string;
  as_of: string | null;
}

export interface Transaction {
  id: number;
  account_id: number;
  external_transaction_id: string;
  transaction_date: string;
  posting_date: string | null;
  merchant_name: string;
  transaction_type: string;
  amount: string;
  currency: string;
  status: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  empty_state_message: string | null;
  freshness: FreshnessInfo;
}
