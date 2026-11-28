import { afterEach, describe, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { screen, within } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import TransactionListPage from './TransactionListPage';
import { jsonResponse, renderWithProviders } from '../test/render';

const unconfirmed = { state: 'unconfirmed freshness', basis: 'b', sourceTime: null, maxAgeSeconds: null };
const tx = (n: number, over: Record<string, unknown> = {}) => ({
  id: `t${n}`, accountId: 'a1', cardId: 'c1', maskedPan: '**** 4821', sourceRef: `TXN-${n}`, transactionStatus: 'Pending',
  transactionTime: '2026-11-22T14:05:00Z', postedDate: null, transactionAmount: '42.15', merchantName: `MERCHANT ${n}`,
  merchantCategoryCode: '5411', eligibleForInstalment: false, freshness: unconfirmed, ...over,
});
const page = (items: unknown[]) => ({ items, total: items.length, limit: 10, offset: 0 });
const acct = { id: 'a1', sourceRef: 'ACC-1001', currency: 'GBP' };

function mockApi(listHandler: () => Response, extra: Record<string, () => Response> = {}) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const path = String(url).replace('/api/v1', '').split('?')[0];
    if (path === '/accounts/a1') return jsonResponse(acct);
    if (path === '/accounts/a1/transactions') return listHandler();
    if (extra[path]) return extra[path]();
    return jsonResponse({ detail: 'Resource not found' }, 404);
  }));
}
const view = () =>
  renderWithProviders(
    <Routes>
      <Route path="/accounts/:accountId/transactions" element={<TransactionListPage />} />
    </Routes>,
    '/accounts/a1/transactions',
  );

afterEach(() => vi.unstubAllGlobals());

describe('TransactionListPage', () => {
  it('lists transactions with separate time and posted date labels, tags and freshness', async () => {
    mockApi(() =>
      jsonResponse(page([tx(1), tx(3, { transactionStatus: 'Posted', postedDate: '2026-11-21', merchantName: 'EXAMPLE' }), tx(4, { eligibleForInstalment: true })])),
    );
    view();
    const table = await screen.findByRole('table', { name: 'Account transactions' });
    const headers = within(table).getAllByRole('columnheader').map((h) => h.textContent);
    expect(headers).toContain('Transaction time');
    expect(headers).toContain('Posted date');
    expect(within(table).getAllByText('Status: Pending')).toHaveLength(2);
    expect(within(table).getByText('Status: Posted')).toBeInTheDocument();
    expect(within(table).getByText('21 Nov 2026')).toBeInTheDocument();
    expect(within(table).getAllByText('Not supplied').length).toBeGreaterThan(0);
    expect(within(table).getAllByText('unconfirmed freshness')).toHaveLength(3);
    expect(within(table).getAllByText('**** 4821')).toHaveLength(3);
    expect(within(table).getByText('Yes')).toBeInTheDocument();
    expect(screen.getByText(/Showing 3 of 3 records/)).toBeInTheDocument();
    expect(screen.getByText('Pending is not posted')).toBeInTheDocument();
  });

  it('shows the record from the detail endpoint on request', async () => {
    mockApi(() => jsonResponse(page([tx(1)])), { '/transactions/t1': () => jsonResponse(tx(1, { merchantName: 'DETAIL MERCHANT' })) });
    view();
    await userEvent.click(await screen.findByRole('button', { name: 'View record TXN-1' }));
    expect(await screen.findByRole('heading', { name: 'Transaction record TXN-1' })).toBeInTheDocument();
    expect(screen.getByText('DETAIL MERCHANT')).toBeInTheDocument();
  });

  it('shows the empty state', async () => {
    mockApi(() => jsonResponse(page([])));
    view();
    expect(await screen.findByText('No transaction records are held for this account in the prototype data.')).toBeInTheDocument();
  });

  it('shows ApiError.detail when transactions cannot be retrieved', async () => {
    mockApi(() => jsonResponse({ detail: 'Resource not found' }, 404));
    view();
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Transactions are unavailable');
    expect(alert).toHaveTextContent('Resource not found');
  });

  it('keeps the last approved records with a warning when a refresh fails', async () => {
    let calls = 0;
    mockApi(() => (++calls === 1 ? jsonResponse(page([tx(1)])) : jsonResponse({ detail: 'Source unavailable' }, 500)));
    view();
    await screen.findByText('MERCHANT 1');
    await userEvent.click(screen.getByRole('button', { name: 'Refresh transactions' }));
    expect(await screen.findByText('Could not refresh transactions')).toBeInTheDocument();
    expect(screen.getByText('MERCHANT 1')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
