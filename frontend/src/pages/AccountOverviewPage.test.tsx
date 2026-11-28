import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import AccountOverviewPage from './AccountOverviewPage';
import { jsonResponse, renderWithProviders } from '../test/render';

const freshness = { state: 'freshness unavailable', basis: 'none', sourceTime: null, maxAgeSeconds: null };
const account = (over: Record<string, unknown> = {}) => ({
  id: 'a1', sourceRef: 'ACC-1001', productName: 'Nationwide Credit Card', accountStatus: 'Open', openedOn: '2021-03-18',
  currency: 'GBP', creditLimit: '10000.00', availableCredit: '5137.65', currentBalance: '4862.35',
  standardPurchaseApr: '22.9', lastStatementBalance: '4701.10', nextStatementDate: '2026-12-05',
  paymentDueDate: '2026-12-30', minimumPayment: '121.56', freshness, informationalNotice: 'n', ...over,
});
const card = (over: Record<string, unknown> = {}) => ({
  id: 'c1', accountId: 'a1', sourceRef: 'CRD-1', maskedPan: '**** 4821', cardStatus: 'Active',
  expiryMonthYear: '2028-09', isDigital: false, ...over,
});
const page = (items: unknown[]) => ({ items, total: items.length, limit: 25, offset: 0 });

function mockApi(routes: Record<string, () => Response>) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const path = String(url).replace('/api/v1', '').split('?')[0];
    const handler = routes[path];
    return handler ? handler() : jsonResponse({ detail: 'Resource not found' }, 404);
  }));
}
const view = () =>
  renderWithProviders(
    <Routes>
      <Route path="/accounts" element={<AccountOverviewPage />} />
      <Route path="/accounts/:accountId" element={<AccountOverviewPage />} />
    </Routes>,
    '/accounts',
  );

afterEach(() => vi.unstubAllGlobals());

describe('AccountOverviewPage', () => {
  it('opens a single account directly with eight unique labels, tags, card and link', async () => {
    mockApi({
      '/accounts': () => jsonResponse(page([account()])),
      '/accounts/a1': () => jsonResponse(account()),
      '/accounts/a1/cards': () => jsonResponse(page([card()])),
    });
    view();
    await screen.findByText('Account status: Open');
    expect(screen.queryByLabelText('Account')).not.toBeInTheDocument();
    const labels = ['Credit limit', 'Available credit', 'Current balance', 'Statement balance', 'Minimum payment',
      'Standard purchase APR', 'Next statement date', 'Payment due date'];
    for (const label of labels) expect(screen.getAllByText(label)).toHaveLength(1);
    expect(screen.getByText('£10,000.00')).toBeInTheDocument();
    expect(screen.getByText('22.9%')).toBeInTheDocument();
    expect(screen.getByText('5 Dec 2026')).toBeInTheDocument();
    expect(screen.getByText('freshness unavailable')).toBeInTheDocument();
    expect(screen.getByText(/Source timestamp for account fields: not supplied/)).toBeInTheDocument();
    expect(await screen.findByText('**** 4821')).toBeInTheDocument();
    expect(screen.getByText('Card status: Active')).toBeInTheDocument();
    expect(screen.getByText('09/2028')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View dated balance breakdown' })).toHaveAttribute('href', '/accounts/a1/balance');
  });

  it('shows Not supplied for null fields and the PendingActivation card verbatim', async () => {
    const sparse = account({ id: 'a3', sourceRef: 'ACC-1003', creditLimit: null, minimumPayment: null, paymentDueDate: null });
    mockApi({
      '/accounts': () => jsonResponse(page([sparse])),
      '/accounts/a3': () => jsonResponse(sparse),
      '/accounts/a3/cards': () => jsonResponse(page([card({ id: 'c3', sourceRef: 'CRD-3', maskedPan: '**** 9040', cardStatus: 'PendingActivation', isDigital: null })])),
    });
    view();
    await screen.findByText('Card status: PendingActivation');
    // three null account fields plus the null digital flag
    expect(screen.getAllByText('Not supplied')).toHaveLength(4);
    expect(screen.getByText('**** 9040')).toBeInTheDocument();
  });

  it('shows a switcher when there are several accounts', async () => {
    const second = account({ id: 'a2', sourceRef: 'ACC-1002' });
    mockApi({
      '/accounts': () => jsonResponse(page([account(), second])),
      '/accounts/a1': () => jsonResponse(account()),
      '/accounts/a1/cards': () => jsonResponse(page([])),
    });
    view();
    const select = await screen.findByLabelText('Account');
    expect(within(select).getAllByRole('option')).toHaveLength(2);
    expect(await screen.findByText('No card is held for this account.')).toBeInTheDocument();
  });

  it('shows the error notice with detail and a Data status link when the account fails', async () => {
    mockApi({
      '/accounts': () => jsonResponse(page([account()])),
      '/accounts/a1': () => jsonResponse({ detail: 'Source unavailable' }, 500),
      '/accounts/a1/cards': () => jsonResponse(page([])),
    });
    view();
    expect(await screen.findByText('Source unavailable')).toBeInTheDocument();
    expect(screen.getByText('Account information is unavailable')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Data status and limitations' })).toHaveAttribute('href', '/data-status');
  });
});
