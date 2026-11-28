import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import LoginPage from './LoginPage';
import { jsonResponse, renderWithProviders } from '../test/render';

const view = () =>
  renderWithProviders(
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/accounts" element={<p>accounts landing</p>} />
    </Routes>,
    '/login',
  );

function mockLogin(status: number, body: unknown = { detail: 'x' }) {
  const fn = vi.fn(async (url: string) => {
    if (String(url).endsWith('/auth/session')) return jsonResponse({ detail: 'Not authenticated' }, 401);
    if (String(url).endsWith('/auth/login')) return jsonResponse(body, status);
    return jsonResponse({ detail: 'Resource not found' }, 404);
  });
  vi.stubGlobal('fetch', fn);
  return fn;
}
afterEach(() => vi.unstubAllGlobals());

const submit = () => userEvent.click(screen.getByRole('button', { name: 'Sign in' }));

describe('LoginPage', () => {
  it('shows both validation messages and sends nothing when empty', async () => {
    const fn = mockLogin(200);
    view();
    await submit();
    expect(await screen.findByText('Enter your username.')).toBeInTheDocument();
    expect(screen.getByText('Enter your password.')).toBeInTheDocument();
    expect(fn.mock.calls.some(([u]) => String(u).endsWith('/auth/login'))).toBe(false);
  });

  it('toggles the password between Show and Hide', async () => {
    mockLogin(200);
    view();
    const toggle = screen.getByRole('button', { name: 'Show' });
    await userEvent.click(toggle);
    expect(screen.getByRole('button', { name: 'Hide' })).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'text');
  });

  it('shows a generic failure that names neither field', async () => {
    mockLogin(401, { detail: 'Invalid credentials' });
    view();
    await userEvent.type(screen.getByLabelText('Username'), 'synthetic.customer01');
    await userEvent.type(screen.getByLabelText('Password'), 'wrong');
    await submit();
    expect(await screen.findByText('Sign-in failed')).toBeInTheDocument();
    expect(screen.getByText('The username or password was not accepted. Check the details and try again.')).toBeInTheDocument();
  });

  it('shows the too-many-attempts notification on HTTP 429', async () => {
    mockLogin(429, { detail: 'Too many' });
    view();
    await userEvent.type(screen.getByLabelText('Username'), 'u');
    await userEvent.type(screen.getByLabelText('Password'), 'p');
    await submit();
    expect(await screen.findByText('Too many sign-in attempts')).toBeInTheDocument();
  });

  it('goes to /accounts after a good login', async () => {
    const login = {
      access_token: 't', token_type: 'Bearer', issued_at: '2026-01-01T00:00:00Z', expires_at: '2026-01-01T01:00:00Z',
      inactivity_timeout_minutes: 15, user: { id: 'u1', username: 'synthetic.customer01', role: 'customer', customer_id: 'c1' },
    };
    mockLogin(200, login);
    view();
    await userEvent.type(screen.getByLabelText('Username'), 'synthetic.customer01');
    await userEvent.type(screen.getByLabelText('Password'), 'Prototype!2026');
    await submit();
    await waitFor(() => expect(screen.getByText('accounts landing')).toBeInTheDocument());
  });
});
