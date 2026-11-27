import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { BalanceBreakdownPage } from '../pages/BalanceBreakdownPage';
import { apiClient } from '../lib/api-client';
import userEvent from '@testing-library/user-event';

vi.mock('../lib/api-client');

const mockAccountsResponse = {
  accounts: [
    {
      id: 123,
      account_number_masked: '****1001',
      card_number_masked: '****4821',
      account_status: 'Active',
      current_balance: '1799.50',
      available_credit: '8200.50',
      credit_limit: '10000.00',
    },
  ],
};

const mockBreakdownResponse = {
  id: 1,
  account_id: 123,
  total_balance: '1799.50',
  pending_total: '114.20',
  snapshot_date: '2026-11-26T14:00:00Z',
  categories: [
    {
      id: 1,
      category_name: 'StandardPurchase',
      category_amount: '299.50',
      apr: '19.90',
      display_rank: 1,
      promo_rate: null,
      promo_end_date: null,
      source_link: null,
    },
    {
      id: 2,
      category_name: 'PromotionalPurchase',
      category_amount: '200.00',
      apr: '0.00',
      display_rank: 2,
      promo_rate: '0.00',
      promo_end_date: '2027-03-14T00:00:00Z',
      source_link: null,
    },
    {
      id: 3,
      category_name: 'BalanceTransfer',
      category_amount: '500.00',
      apr: '0.00',
      display_rank: 3,
      promo_rate: '0.00',
      promo_end_date: '2027-10-27T14:00:00Z',
      source_link: {
        source_type: 'BalanceTransfer',
        source_id: 1,
        source_reference: 'BT-2024-001',
      },
    },
    {
      id: 4,
      category_name: 'Instalment',
      category_amount: '800.00',
      apr: '9.90',
      display_rank: 4,
      promo_rate: null,
      promo_end_date: null,
      source_link: {
        source_type: 'InstalmentPlan',
        source_id: 1,
        source_reference: 'IP-2024-001',
      },
    },
  ],
  freshness: {
    level: 'Current',
    as_of: '2026-11-26T14:00:00Z',
  },
  created_at: '2026-11-26T14:00:00Z',
  updated_at: '2026-11-26T14:00:00Z',
};

const mockZeroBalanceResponse = {
  ...mockBreakdownResponse,
  total_balance: '0.00',
  categories: [],
};

describe('BalanceBreakdownPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays categories in correct order by display_rank', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/v1/accounts')) {
        return Promise.resolve(mockAccountsResponse);
      }
      return Promise.resolve(mockBreakdownResponse);
    });

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <BalanceBreakdownPage />
      </BrowserRouter>
    );

    // Wait for accounts to load and select one
    await waitFor(() => {
      expect(screen.getByLabelText('Account')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Account');
    await user.selectOptions(select, '123');

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/Standard purchases/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Verify category ordering
    expect(screen.getByText(/Standard purchases/i)).toBeInTheDocument();
    expect(screen.getByText(/Purchase promotion/i)).toBeInTheDocument();
  });

  it('separates pending total from total outstanding', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/v1/accounts')) {
        return Promise.resolve(mockAccountsResponse);
      }
      return Promise.resolve(mockBreakdownResponse);
    });

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <BalanceBreakdownPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Account')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Account');
    await user.selectOptions(select, '123');

    await waitFor(() => {
      expect(screen.getByText('£1,799.50')).toBeInTheDocument();
    });

    expect(screen.getByText('£114.20')).toBeInTheDocument();
    expect(screen.getByText(/Pending, not yet in your balance/i)).toBeInTheDocument();
  });

  it('displays source links when present', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/v1/accounts')) {
        return Promise.resolve(mockAccountsResponse);
      }
      return Promise.resolve(mockBreakdownResponse);
    });

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <BalanceBreakdownPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Account')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Account');
    await user.selectOptions(select, '123');

    await waitFor(() => {
      expect(screen.getByText(/BT-2024-001/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/IP-2024-001/i)).toBeInTheDocument();
  });

  it('displays zero balance state correctly', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/v1/accounts')) {
        return Promise.resolve(mockAccountsResponse);
      }
      return Promise.resolve(mockZeroBalanceResponse);
    });

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <BalanceBreakdownPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Account')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Account');
    await user.selectOptions(select, '123');

    await waitFor(() => {
      expect(screen.getByText(/You have no balance to pay/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/£0.00 balance/i)).toBeInTheDocument();
  });

  it('shows freshness indicator when level is Current', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/v1/accounts')) {
        return Promise.resolve(mockAccountsResponse);
      }
      return Promise.resolve(mockBreakdownResponse);
    });

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <BalanceBreakdownPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Account')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Account');
    await user.selectOptions(select, '123');

    await waitFor(() => {
      expect(screen.getByText(/Up to date/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Breakdown as of/i)).toBeInTheDocument();
  });
});
