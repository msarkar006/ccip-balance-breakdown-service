export interface User {
  id: number;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  session_id: number;
  session_expires_at: string;
  step_up_verified_at: string | null;
  selected_account_id: number | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}
