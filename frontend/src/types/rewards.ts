export interface RewardsProgramme {
  programme_name: string;
  points_balance: number;
  status: string;
  as_of: string;
}

export interface FreshnessInfo {
  level: string;
  as_of: string;
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

export interface RewardsSummaryResponse {
  programme: RewardsProgramme | null;
  relevant_offers: Offer[];
  freshness: FreshnessInfo;
}
