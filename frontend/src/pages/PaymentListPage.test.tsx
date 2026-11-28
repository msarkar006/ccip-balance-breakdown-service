import { afterEach, describe, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { screen, within } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import PaymentListPage from './PaymentListPage';
import { jsonResponse, renderWithProviders } from '../test/render';

const none = { state: 'freshness unavailable', basis: 'b', sourceTime: null, maxAgeSeconds: null };
const NOTICE = 'Information about this existing record only.';
const pay = (n: number, over: Record<string, unknown> = {}) => ({
  id: `p${n}`, accountId: 'a1', sourceRef: `PMT-${n}`, viaMandateRef: null, paymentType: 'OneOff', paymentMethod: 'FasterPayments',
  paymentStatus: 'Completed', paymentAmount: '500.00', paymentDate: '2026-11-24', sourceBankName: 'Nationwide Current Account',
  sourceMaskedAccount: '****1234', freshness: none, informationalNotice: NOTICE, ...over,
});
const page = (items: unknown[]) => ({ items, total: items.length, limit: 10, offset: 0 });
const acct = { id: 'a1', sourceRef: 'ACC-1001', currency: 'GBP' };

function mockApi(listHandler: () => Response, extra: Record<string, () => Response> = {}) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const path = String(url).replace('/api/v1', '').split('?')[0];
    if (path === '/accounts/a1') return jsonResponse(acct);
    if (path === '/accounts/a1/payments') return listHandler();
    if (extra[path]) return extra[path]();
    return jsonResponse({ detail: 'Resource not found' }, 404);
  }));
}
const view = () =>
  renderWithProviders(
    <Routes>
      <Route path="/accounts/:accountId/payments" element={<PaymentListPage />} />
    </Routes>,
    '/accounts/a1/payments',
  );

afterEach(() => vi.unstubAllGlobals());

describe('PaymentListPage', () => {
  it('shows each payment with verbatim type and status, masked account, mandate text and its notice', async () => {
    mockApi(() =>
      jsonResponse(page([pay(1), pay(4, { paymentType: 'Scheduled', paymentStatus: 'Submitted' }), pay(6, { paymentType: 'DirectDebitCollection', paymentMethod: 'DirectDebit', viaMandateRef: 'MND-1' })])),
    );
    view();
    const table = await screen.findByRole('table', { name: 'Payment history' });
    expect(within(table).getByText('Type: Scheduled')).toBeInTheDocument();
    expect(within(table).getByText('Status: Submitted')).toBeInTheDocument();
    expect(within(table).getByText('Type: DirectDebitCollection')).toBeInTheDocument();
    expect(within(table).getByText('MND-1')).toBeInTheDocument();
    expect(within(table).getAllByText('None')).toHaveLength(2);
    expect(within(table).getAllByText('****1234')).toHaveLength(3);
    expect(within(table).getAllByText(NOTICE)).toHaveLength(3);
    expect(screen.getByText('freshness unavailable')).toBeInTheDocument();
    expect(screen.getByText(/Showing 3 of 3 payments/)).toBeInTheDocument();
  });

  it('has no control that acts on a payment', async () => {
    mockApi(() => jsonResponse(page([pay(1)])));
    view();
    await screen.findByRole('table');
    const names = screen.getAllByRole('button').map((b) => b.textContent ?? '');
    for (const name of names) expect(name).not.toMatch(/\b(pay|cancel|schedule|amend|complete|submit)\b/i);
  });

  it('shows the record from the detail endpoint on request', async () => {
    mockApi(() => jsonResponse(page([pay(1)])), { '/payments/p1': () => jsonResponse(pay(1, { sourceBankName: 'Detail Bank' })) });
    view();
    await userEvent.click(await screen.findByRole('button', { name: 'View record PMT-1' }));
    expect(await screen.findByRole('heading', { name: 'Payment record PMT-1' })).toBeInTheDocument();
    expect(screen.getByText('Detail Bank')).toBeInTheDocument();
  });

  it('shows the empty state', async () => {
    mockApi(() => jsonResponse(page([])));
    view();
    expect(await screen.findByText('No payment records are held for this account in the prototype data.')).toBeInTheDocument();
  });

  it('shows ApiError.detail when payments cannot be retrieved', async () => {
    mockApi(() => jsonResponse({ detail: 'Resource not found' }, 404));
    view();
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Payment information is unavailable');
    expect(alert).toHaveTextContent('Resource not found');
  });

  it('keeps the last approved records with a warning when a refresh fails', async () => {
    let calls = 0;
    mockApi(() => (++calls === 1 ? jsonResponse(page([pay(1)])) : jsonResponse({ detail: 'Source unavailable' }, 500)));
    view();
    await screen.findByText('Status: Completed');
    await userEvent.click(screen.getByRole('button', { name: 'Refresh payments' }));
    expect(await screen.findByText('Could not refresh payment records')).toBeInTheDocument();
    expect(screen.getByText('Status: Completed')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
