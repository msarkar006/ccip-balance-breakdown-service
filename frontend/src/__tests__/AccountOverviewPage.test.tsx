import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AccountOverviewPage } from '../pages/AccountOverviewPage';
import { AuthProvider } from '../lib/auth-context';
import { apiClient } from '../lib/api-client';

vi.mock('../lib/api-client');

const renderAccountOverviewPage = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <AccountOverviewPage />
      </AuthProvider>
    </BrowserRouter>
  );
};

const mockAccounts = {
  accounts: [
    { id: 1, account_number_masked: '****1001', account_status: 'Active', current_balance: '1799.50', available_credit: '3200.50', credit_limit: '5000.00' },
    { id: 2, account_number_masked: '****1002', account_status: 'Active', current_balance: '2150.00', available_credit: '7850.00', credit_limit: '10000.00' },
  ],
};

const mockOverview = {
  id: 1,
  account_number_masked: '****1001',
  sort_code_masked: '12-34-56',
  account_status: 'Active',
  credit_limit: '5000.00',
  available_credit: '3200.50',
  current_balance: '1799.50',
  minimum_payment_due: '89.98',
  payment_due_date: '2026-12-11T00:00:00Z',
  cards: [
    {
      id: 1,
      card_number_masked: '****-****-****-1001',
      card_type: 'Visa',
      card_status: 'Active',
      expiry_month: 12,
      expiry_year: 2026,
    },
  ],
  freshness: 'Current',
  as_of: '2026-11-26T12:00:00Z',
  show_as_of_cue: true,
};

describe('AccountOverviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders account overview heading', async () => {
    vi.mocked(apiClient.get)
      .mockResolvedValueOnce(mockAccounts)
      .mockResolvedValueOnce(mockOverview);
    vi.mocked(apiClient.put).mockResolvedValue({ success: true });

    renderAccountOverviewPage();

    expect(await screen.findByText('Account overview', {}, { timeout: 5000 })).toBeInTheDocument();
  });

  it('renders account selector', async () => {
    vi.mocked(apiClient.get)
      .mockResolvedValueOnce(mockAccounts)
      .mockResolvedValueOnce(mockOverview);
    vi.mocked(apiClient.put).mockResolvedValue({ success: true });

    renderAccountOverviewPage();

    expect(await screen.findByLabelText(/account/i, {}, { timeout: 5000 })).toBeInTheDocument();
  });
});
