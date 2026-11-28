import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { get, onUnauthorized, post, setAccessToken } from './api-client';
import type { LoginRequest, LoginResponse, SessionInfo, UserSummary } from '../types/auth';

const TOKEN_KEY = 'ccip.accessToken';

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous';

export interface AuthContextValue {
  status: AuthStatus;
  user: UserSummary | null;
  /** True after a signed-in session ended (sign out, inactivity or expiry). */
  sessionEnded: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredToken(): string | null {
  try {
    return window.sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function storeToken(token: string | null): void {
  try {
    if (token) window.sessionStorage.setItem(TOKEN_KEY, token);
    else window.sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: the session lasts for this page load only */
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [initialToken] = useState(readStoredToken);
  const [status, setStatus] = useState<AuthStatus>(initialToken ? 'loading' : 'anonymous');
  const [user, setUser] = useState<UserSummary | null>(null);
  const [sessionEnded, setSessionEnded] = useState(false);

  const clear = useCallback((ended: boolean) => {
    setAccessToken(null);
    storeToken(null);
    setUser(null);
    setStatus('anonymous');
    if (ended) setSessionEnded(true);
  }, []);

  useEffect(() => {
    onUnauthorized(() => clear(true));
    return () => onUnauthorized(null);
  }, [clear]);

  useEffect(() => {
    if (!initialToken) return;
    let cancelled = false;
    setAccessToken(initialToken);
    get<SessionInfo>('/auth/session')
      .then((info) => {
        if (cancelled) return;
        setUser(info.user);
        setStatus('authenticated');
      })
      .catch(() => {
        if (!cancelled) clear(false);
      });
    return () => {
      cancelled = true;
    };
  }, [initialToken, clear]);

  const login = useCallback(async (credentials: LoginRequest) => {
    const response = await post<LoginResponse>('/auth/login', credentials);
    setAccessToken(response.accessToken);
    storeToken(response.accessToken);
    setUser(response.user);
    setSessionEnded(false);
    setStatus('authenticated');
  }, []);

  const logout = useCallback(async () => {
    try {
      await post<void>('/auth/logout');
    } catch {
      /* the session is cleared locally either way */
    }
    clear(true);
  }, [clear]);

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, sessionEnded, login, logout }),
    [status, user, sessionEnded, login, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
