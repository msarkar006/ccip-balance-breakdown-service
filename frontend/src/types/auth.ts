export type Role = 'customer' | 'administrator';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface UserSummary {
  id: string;
  username: string;
  role: Role;
  customerId: string | null;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: 'Bearer';
  issuedAt: string;
  expiresAt: string;
  inactivityTimeoutMinutes: number;
  user: UserSummary;
}

export interface SessionInfo {
  user: UserSummary;
  issuedAt: string;
  expiresAt: string;
  lastActivityAt: string;
}
