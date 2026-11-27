import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import { AuthProvider } from '../lib/auth-context';
import { apiClient } from '../lib/api-client';

vi.mock('../lib/api-client');

const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it('renders login form with username and password fields', () => {
    renderLoginPage();

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
  });

  it('shows validation errors when fields are empty', async () => {
    const user = userEvent.setup();
    renderLoginPage();

    // Clear the default values
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    await user.clear(usernameInput);
    await user.clear(passwordInput);

    const loginButton = screen.getByRole('button', { name: /log in/i });
    await user.click(loginButton);

    expect(await screen.findByText('Enter your username')).toBeInTheDocument();
    expect(await screen.findByText('Enter your password')).toBeInTheDocument();
  });

  it('submits login form with correct credentials', async () => {
    const user = userEvent.setup();

    vi.mocked(apiClient.post).mockResolvedValue({
      access_token: 'test-token',
      user: { id: 1, email: 'admin@example.com', is_active: true, is_superuser: true },
    });

    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const loginButton = screen.getByRole('button', { name: /log in/i });

    await user.clear(usernameInput);
    await user.clear(passwordInput);
    await user.type(usernameInput, 'admin@example.com');
    await user.type(passwordInput, 'admin123');
    await user.click(loginButton);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/v1/auth/login', {
        email: 'admin@example.com',
        password: 'admin123',
      });
    });
  });

  it('shows error on failed login', async () => {
    const user = userEvent.setup();

    vi.mocked(apiClient.post).mockRejectedValue(new Error('Invalid credentials'));

    renderLoginPage();

    const loginButton = screen.getByRole('button', { name: /log in/i });
    await user.click(loginButton);

    // Wait for the notification to appear
    await waitFor(async () => {
      const notifications = screen.queryAllByRole('status');
      expect(notifications.length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });
});
