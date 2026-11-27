export interface BalanceTransfer {
  id: number;
  external_transfer_id: string;
  transfer_amount: string;
  promotional_rate: string;
  status: string;
  requested_on: string;
  processed_at: string | null;
}

export interface BalanceTransferListResponse {
  items: BalanceTransfer[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface TrackerMilestone {
  event_type: string;
  status: string;
  occurred_at: string;
  event_data: string;
}

export interface PromotionalContext {
  promo_rate: string;
  promo_start_date: string;
  promo_end_date: string;
  revert_rate: string | null;
}

export interface SourceLink {
  source_type: string;
  source_id: number;
  source_reference: string;
  category_id: number;
  category_name: string;
}

export interface Guidance {
  message_code: string;
  message: string;
  next_step: string;
}

export interface BalanceTransferDetail {
  id: number;
  account_id: number;
  external_transfer_id: string;
  transfer_amount: string;
  status: string;
  requested_on: string;
  processed_at: string | null;
  timeline: TrackerMilestone[];
  promotional_context: PromotionalContext | null;
  source_link: SourceLink | null;
  guidance: Guidance | null;
  created_at: string;
  updated_at: string;
}

export interface BalanceTransferInitiationRequest {
  account_id: number;
  offer_code: string;
  transfer_amount: number;
  external_card_last4: string;
  provider_name: string;
  idempotency_key: string;
}

export interface BalanceTransferInitiationResponse {
  id: number;
  external_transfer_id: string;
  transfer_amount: string;
  status: string;
  guidance: Guidance | null;
  idempotent_replay: boolean;
}

export interface MoneyTransfer {
  id: number;
  external_transfer_id: string;
  payee_name: string;
  amount: string;
  currency: string;
  status: string;
  requested_on: string;
  processed_at: string | null;
}

export interface MoneyTransferListResponse {
  items: MoneyTransfer[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface PayeeDetail {
  payee_id: number;
  payee_name: string;
  account_number_masked: string;
  sort_code_masked: string;
}

export interface MoneyTransferDetail {
  id: number;
  account_id: number;
  external_transfer_id: string;
  payee: PayeeDetail;
  amount: string;
  currency: string;
  fee_context: string | null;
  status: string;
  requested_on: string;
  processed_at: string | null;
  timeline: TrackerMilestone[];
  guidance: Guidance | null;
  created_at: string;
  updated_at: string;
}

export interface Payee {
  id: number;
  payee_name: string;
  account_number_masked: string;
  sort_code_masked: string;
  created_at: string;
}

export interface PayeeListResponse {
  items: Payee[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface MoneyTransferInitiationRequest {
  account_id: number;
  payee_id: number;
  amount: number;
  currency: string;
  idempotency_key: string;
}

export interface MoneyTransferInitiationResponse {
  id: number;
  external_transfer_id: string;
  amount: string;
  currency: string;
  status: string;
  guidance: Guidance | null;
  idempotent_replay: boolean;
}

export interface Offer {
  id: number;
  offer_code: string;
  offer_title: string;
  offer_description: string;
  offer_type: string;
  status: string;
  valid_from: string;
  valid_until: string | null;
}

export interface OfferListResponse {
  items: Offer[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
