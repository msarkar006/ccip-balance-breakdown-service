import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { AuthProvider } from '../lib/auth-context';
import { jsonResponse } from './render';

const USER = { id: 'u1', username: 'synthetic.customer01', role: 'customer', customerId: 'c1' };
const ACCOUNT = {
  id: '11111111-1111-1111-1111-111111111111',
  sourceRef: 'ACC-1001',
  productName: 'Card',
  accountStatus: 'Open',
  currency: 'GBP',
  freshness: { state: 'freshness unavailable', basis: 'none' },
  informationalNotice: 'info',
};

function mockApi(sessionOk: boolean) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const url = String(input);
    const method = (init as RequestInit | undefined)?.method ?? 'GET';
    if (url.endsWith('/auth/login')) {
      return jsonResponse({ accessToken: 't', tokenType: 'Bearer', issuedAt: '', expiresAt: '', inactivityTimeoutMinutes: 15, user: USER });
    }
    if (url.endsWith('/auth/logout')) return jsonResponse(null, 204);
    if (url.endsWith('/auth/session')) {
      return sessionOk ? jsonResponse({ user: USER, issuedAt: '', expiresAt: '', lastActivityAt: '' }) : jsonResponse({ detail: 'Authentication required' }, 401);
    }
    if (url.includes('/accounts/')) return jsonResponse(ACCOUNT);
    if (url.includes('/accounts')) return jsonResponse({ items: [ACCOUNT], total: 1, limit: 1, offset: 0 });
    throw new Error(`unexpected ${method} ${url}`);
  });
}

function renderApp(route: string) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe('routing and auth guard', () => {
  it.each(['/accounts', '/accounts/abc/balance', '/data-rights', '/nowhere'])('sends anonymous %s to the sign-in page', async (route) => {
    mockApi(false);
    renderApp(route);
    expect(await screen.findByRole('heading', { name: 'Sign in', level: 1 })).toBeInTheDocument();
  });

  it('shows the shell with all nav entries after a form sign-in, and signs out again', async () => {
    mockApi(true);
    const user = userEvent.setup();
    renderApp('/login');
    await user.type(screen.getByLabelText('Username'), 'synthetic.customer01');
    await user.type(screen.getByLabelText('Password'), 'Prototype!2026');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByRole('heading', { name: 'Account overview', level: 1 })).toBeInTheDocument();
    expect(screen.getByText('Read-only prototype using synthetic data')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Signed in as synthetic.customer01' })).toBeInTheDocument();
    const nav = screen.getByRole('navigation', { name: 'Side navigation' });
    for (const name of ['Account overview', 'Balance breakdown', 'Transactions', 'Payments', 'Data status and limitations', 'Your data rights', 'Sign out']) {
      expect(within(nav).getByRole('link', { name })).toBeInTheDocument();
    }
    await waitFor(() => expect(within(nav).getByRole('link', { name: 'Transactions' })).toHaveAttribute('href', `/accounts/${ACCOUNT.id}/transactions`));

    await user.click(within(nav).getByRole('link', { name: 'Sign out' }));
    expect(await screen.findByRole('heading', { name: 'Sign in', level: 1 })).toBeInTheDocument();
    expect(screen.getByText('You have been signed out')).toBeInTheDocument();
  });

  it('shows the failed and throttled states from the API without naming which field was wrong', async () => {
    const spy = mockApi(false);
    const user = userEvent.setup();
    renderApp('/login');
    spy.mockResolvedValueOnce(jsonResponse({ detail: 'Invalid username or password' }, 401));
    await user.type(screen.getByLabelText('Username'), 'x');
    await user.type(screen.getByLabelText('Password'), 'y');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByText('Sign-in failed')).toBeInTheDocument();
    spy.mockResolvedValueOnce(jsonResponse({ detail: 'Too many sign-in attempts' }, 429, { 'Retry-After': '60' }));
    await user.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByText('Too many sign-in attempts')).toBeInTheDocument();
  });

  it('redirects an unknown path to /accounts when signed in', async () => {
    window.sessionStorage.setItem('ccip.accessToken', 't');
    mockApi(true);
    renderApp('/nowhere');
    expect(await screen.findByRole('heading', { name: 'Account overview', level: 1 })).toBeInTheDocument();
  });
});
