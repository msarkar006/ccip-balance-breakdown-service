export interface Account {
  id: number;
  account_number_masked: string;
  account_status: string;
  current_balance: string;
  available_credit: string;
  credit_limit: string;
  card_number_masked?: string;
}

export interface CreditCard {
  id: number;
  card_number_masked: string;
  card_type: string;
  card_status: string;
  expiry_month: number;
  expiry_year: number;
}

export interface AccountOverview {
  id: number;
  account_number_masked: string;
  sort_code_masked: string;
  account_status: string;
  credit_limit: string;
  available_credit: string;
  current_balance: string;
  minimum_payment_due: string;
  payment_due_date: string;
  cards: CreditCard[];
  freshness: string;
  as_of?: string;
  show_as_of_cue?: boolean;
}

export interface Transaction {
  id: number;
  merchant: string;
  transaction_date: string;
  posting_date: string | null;
  amount: string;
  status: 'Pending' | 'Posted';
}

export interface AccountListResponse {
  accounts: Account[];
}

export interface AccountSelectionRequest {
  account_id: number | null;
}

export interface AccountSelectionResponse {
  success: boolean;
  selected_account_id: number | null;
  message: string;
}
