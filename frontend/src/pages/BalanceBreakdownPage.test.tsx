import { afterEach, describe, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { screen, within } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import BalanceBreakdownPage from './BalanceBreakdownPage';
import { jsonResponse, renderWithProviders } from '../test/render';

const fresh = { state: 'unconfirmed freshness', basis: 'b', sourceTime: '2026-11-24T08:15:00Z', maxAgeSeconds: null };
const none = { state: 'freshness unavailable', basis: 'b', sourceTime: null, maxAgeSeconds: null };
const cat = (rank: number, over: Record<string, unknown> = {}) => ({
  id: `k${rank}`, sourceRef: `CAT-${rank}`, categoryType: 'StandardPurchase', categoryLabel: `Label ${rank}`, displayRank: rank,
  categoryBalance: '10.00', categoryAprPercent: '22.9', promoEndDate: null, revertRatePercent: null, daysToExpiry: null,
  sourceBalanceTransferRef: null, sourceInstalmentPlanRef: null, ...over,
});
const detail = (over: Record<string, unknown> = {}) => ({
  id: 'b1', accountId: 'a1', sourceRef: 'BBD-1', asOf: '2026-11-24T08:15:00Z', totalOutstanding: '4862.35', pendingTotal: '114.20',
  isZeroBalance: false, purchasesSubtotal: '1852.10', balanceTransfersSubtotal: '3010.25', categories: [], freshness: fresh,
  notice: 'n', ...over,
});
const summary = { id: 'b1', accountId: 'a1', sourceRef: 'BBD-1', asOf: null, freshness: fresh };
const list = { items: [summary], total: 1, limit: 1, offset: 0 };
const acct = { id: 'a1', sourceRef: 'ACC-1001', currency: 'GBP' };

function mockApi(detailHandler: () => Response) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const path = String(url).replace('/api/v1', '').split('?')[0];
    if (path === '/accounts/a1') return jsonResponse(acct);
    if (path === '/accounts/a1/balance-breakdowns') return jsonResponse(list);
    if (path === '/balance-breakdowns/b1') return detailHandler();
    return jsonResponse({ detail: 'Resource not found' }, 404);
  }));
}
const view = () =>
  renderWithProviders(
    <Routes>
      <Route path="/accounts/:accountId/balance" element={<BalanceBreakdownPage />} />
    </Routes>,
    '/accounts/a1/balance',
  );

afterEach(() => vi.unstubAllGlobals());

describe('BalanceBreakdownPage', () => {
  it('shows asOf, freshness state, separate totals and ranked categories with qualifiers', async () => {
    const categories = [
      cat(2, { categoryType: 'BalanceTransfer', categoryLabel: 'Balance transfer 1', promoEndDate: '2027-06-30', revertRatePercent: '22.9', daysToExpiry: 218, sourceBalanceTransferRef: 'BT-1' }),
      cat(1, { categoryLabel: 'Standard purchases' }),
      cat(3, { categoryType: 'Instalment', categoryLabel: 'Instalment plan IP-66', sourceInstalmentPlanRef: 'IP-66' }),
    ];
    mockApi(() => jsonResponse(detail({ categories })));
    view();
    expect(await screen.findByText('unconfirmed freshness')).toBeInTheDocument();
    expect(screen.getAllByText('24 Nov 2026, 08:15 UTC', { selector: 'time' }).length).toBeGreaterThan(0);
    for (const label of ['Total outstanding', 'Pending total', 'Purchases subtotal', 'Balance transfers subtotal', 'Zero balance (source field)'])
      expect(screen.getAllByText(label)).toHaveLength(1);
    expect(screen.getByText('£4,862.35')).toBeInTheDocument();
    expect(screen.getByText('£114.20')).toBeInTheDocument();
    const rows = within(screen.getByRole('list', { name: /Balance categories/ })).getAllByRole('heading', { level: 3 });
    expect(rows.map((r) => r.textContent)).toEqual(['Standard purchases', 'Balance transfer 1', 'Instalment plan IP-66']);
    expect(screen.getByText('BT-1')).toBeInTheDocument();
    expect(screen.getByText('IP-66', { selector: 'span' })).toBeInTheDocument();
    expect(screen.getByText('30 Jun 2027')).toBeInTheDocument();
  });

  it('keeps pending total visible for a zero balance (BBD-2)', async () => {
    mockApi(() => jsonResponse(detail({ sourceRef: 'BBD-2', totalOutstanding: '0.00', pendingTotal: '4.80', isZeroBalance: true, purchasesSubtotal: null, balanceTransfersSubtotal: null })));
    view();
    expect(await screen.findByText('£4.80')).toBeInTheDocument();
    expect(screen.getByText('£0.00')).toBeInTheDocument();
    expect(screen.getByText('Yes')).toBeInTheDocument();
    expect(screen.getAllByText('Not supplied')).toHaveLength(2);
    expect(screen.getByText(/Zero balance does not remove the pending total/)).toBeInTheDocument();
  });

  it('prints freshness unavailable and "not supplied" when the source time is missing', async () => {
    mockApi(() => jsonResponse(detail({ asOf: null, freshness: none })));
    view();
    expect(await screen.findByText('freshness unavailable')).toBeInTheDocument();
    expect(screen.getByText(/As of not supplied/)).toBeInTheDocument();
  });

  it('shows ErrorNotice detail when the breakdown cannot be loaded', async () => {
    mockApi(() => jsonResponse({ detail: 'Resource not found' }, 404));
    view();
    expect(await screen.findByRole('alert')).toHaveTextContent('Resource not found');
  });

  it('keeps the last approved snapshot with a warning when a refresh fails', async () => {
    let calls = 0;
    mockApi(() => (++calls === 1 ? jsonResponse(detail()) : jsonResponse({ detail: 'Source unavailable' }, 500)));
    view();
    await screen.findByText('£4,862.35');
    await userEvent.click(screen.getByRole('button', { name: 'Refresh breakdown' }));
    expect(await screen.findByText('Could not refresh this breakdown')).toBeInTheDocument();
    expect(screen.getByText('£4,862.35')).toBeInTheDocument();
    expect(screen.getByText('unconfirmed freshness')).toBeInTheDocument();
  });
});
