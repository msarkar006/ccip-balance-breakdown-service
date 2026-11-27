export interface TrackerItem {
  entity_type: 'Payment' | 'MoneyTransfer' | 'BalanceTransfer' | 'DirectDebitChangeRequest';
  entity_id: string;
  title: string;
  lifecycle_state: string;
  status_label: string;
  is_final: boolean;
  amount: string | null;
  last_updated_at: string;
  freshness: {
    level: string;
    as_of: string | null;
  };
  escalation: {
    is_escalated: boolean;
    reason: string;
    guidance: string;
  } | null;
  guidance: {
    message_code: string;
    message: string;
    next_step: string;
  } | null;
  resource_path: string;
}

export interface TrackerListResponse {
  items: TrackerItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  unresolved_count: number;
  overall_message: string | null;
}

export interface TrackerMilestone {
  event_timestamp: string;
  milestone_label: string;
  detail: string;
}

export interface TrackerDetailResponse {
  tracker_item: TrackerItem;
  milestones: TrackerMilestone[];
  timeline_freshness: {
    level: string;
    as_of: string | null;
  };
}

export interface TrackerRefreshResponse {
  tracker_item: TrackerItem;
  refresh_outcome: 'updated' | 'unchanged' | 'failed';
  refresh_message: string;
}
