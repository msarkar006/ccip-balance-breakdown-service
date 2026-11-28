import { useCallback, useEffect, useState } from 'react';
import { ApiError, get, withQuery, type QueryParams } from './api-client';
import type { Account, AccountPage, BalanceBreakdown, BalanceBreakdownSummaryPage, CardPage } from '../types/account';
import type { PaymentPage, TrackingEventPage, TransactionPage } from '../types/activity';

export interface QueryState<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  reload: () => void;
}

/** Fetches `path` (GET only). A null path skips the request. Re-runs when path or params change. */
export function useApiQuery<T>(path: string | null, params?: QueryParams): QueryState<T> {
  const url = path === null ? null : withQuery(path, params);
  const [state, setState] = useState<{ data: T | null; error: ApiError | null; loading: boolean }>({
    data: null,
    error: null,
    loading: url !== null,
  });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (url === null) {
      setState({ data: null, error: null, loading: false });
      return;
    }
    let cancelled = false;
    setState((previous) => ({ ...previous, error: null, loading: true }));
    get<T>(url)
      .then((data) => {
        if (!cancelled) setState({ data, error: null, loading: false });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        const apiError = error instanceof ApiError ? error : new ApiError(0, 'Something went wrong. Try again later.');
        setState({ data: null, error: apiError, loading: false });
      });
    return () => {
      cancelled = true;
    };
  }, [url, nonce]);

  const reload = useCallback(() => setNonce((value) => value + 1), []);
  return { ...state, reload };
}

export interface PageParams extends QueryParams {
  limit?: number;
  offset?: number;
}

export const useAccounts = (params?: PageParams, enabled = true) =>
  useApiQuery<AccountPage>(enabled ? '/accounts' : null, params);
export const useAccount = (accountId: string | undefined) =>
  useApiQuery<Account>(accountId ? `/accounts/${accountId}` : null);
export const useCards = (accountId: string | undefined) =>
  useApiQuery<CardPage>(accountId ? `/accounts/${accountId}/cards` : null);
export const useBalanceBreakdowns = (accountId: string | undefined, params?: PageParams) =>
  useApiQuery<BalanceBreakdownSummaryPage>(accountId ? `/accounts/${accountId}/balance-breakdowns` : null, params);
export const useBalanceBreakdown = (breakdownId: string | undefined) =>
  useApiQuery<BalanceBreakdown>(breakdownId ? `/balance-breakdowns/${breakdownId}` : null);
export const useTransactions = (accountId: string | undefined, params?: PageParams) =>
  useApiQuery<TransactionPage>(accountId ? `/accounts/${accountId}/transactions` : null, params);
export const usePayments = (accountId: string | undefined, params?: PageParams) =>
  useApiQuery<PaymentPage>(accountId ? `/accounts/${accountId}/payments` : null, params);
export const useTrackingEvents = (accountId: string | undefined, params?: PageParams) =>
  useApiQuery<TrackingEventPage>(accountId ? `/accounts/${accountId}/tracking-events` : null, params);
