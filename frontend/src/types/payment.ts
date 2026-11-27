export interface PaymentGuidance {
  minimum_payment: string;
  due_date: string;
  current_balance: string;
  max_payment_amount: string;
  direct_debit_coverage: DirectDebitCoverage;
}

export interface DirectDebitCoverage {
  coverage_status: 'expected_to_cover' | 'not_expected_to_cover' | 'cannot_be_confirmed';
  manual_payment_may_be_required: boolean;
  reason: string;
}

export interface PaymentListItem {
  id: number;
  account_id: number;
  external_payment_id: string;
  idempotency_key: string | null;
  payment_type: 'OneOff' | 'Scheduled' | 'DirectDebitCollection';
  payment_method: string;
  amount: string;
  currency: string;
  status: 'Submitted' | 'Processing' | 'Completed' | 'Failed' | 'Cancelled' | 'Restricted';
  scheduled_date: string | null;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentListResponse {
  items: PaymentListItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  empty_state_message: string | null;
  freshness: {
    level: string;
    as_of: string | null;
  };
}

export interface TrackerMilestone {
  event_type: string;
  status: string;
  event_timestamp: string;
  description: string;
}

export interface GuidanceInfo {
  message_code: string;
  message: string;
  next_step: string;
}

export interface PaymentDetail {
  payment: PaymentListItem;
  timeline: TrackerMilestone[];
  can_cancel: boolean;
  cancellation_message: string;
  guidance: GuidanceInfo | null;
}

export interface PaymentInitiationRequest {
  account_id: number;
  amount: string;
  currency: string;
  payment_method: string;
  scheduled_date: string | null;
  idempotency_key: string;
}

export interface PaymentInitiationResponse {
  id: number;
  account_id: number;
  external_payment_id: string;
  idempotency_key: string;
  amount: string;
  currency: string;
  status: string;
  scheduled_date: string | null;
  created_at: string;
  guidance: GuidanceInfo | null;
  idempotent_replay?: boolean;
}
