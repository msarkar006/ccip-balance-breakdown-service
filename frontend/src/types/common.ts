/** Shared wire types. Field names mirror openapi.yaml (camelCase). Money and percent are strings. */

export type Money = string;
export type Percent = string;

export type FreshnessState = 'freshness unavailable' | 'unconfirmed freshness' | 'stale';

export interface Freshness {
  state: FreshnessState;
  basis: string;
  sourceTime?: string | null;
  maxAgeSeconds?: number | null;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ErrorResponse {
  detail: string;
}

export interface HealthStatus {
  status: 'ok';
}
