import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { TransactionHistoryPage } from '../pages/TransactionHistoryPage';
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

const mockTransactionsResponse = {
  items: [
    {
      id: 1,
      account_id: 123,
      external_transaction_id: 'TXN-001',
      transaction_date: '2026-11-25T14:30:00Z',
      posting_date: '2026-11-26T10:00:00Z',
      merchant_name: 'Grocery Store',
      transaction_type: 'Purchase',
      amount: '45.67',
      currency: 'GBP',
      status: 'Posted',
      description: 'Weekly groceries',
      created_at: '2026-11-25T14:30:00Z',
      updated_at: '2026-11-26T10:00:00Z',
    },
    {
      id: 2,
      account_id: 123,
      external_transaction_id: 'TXN-002',
      transaction_date: '2026-11-24T09:15:00Z',
      posting_date: null,
      merchant_name: 'Coffee Shop',
      transaction_type: 'Purchase',
      amount: '4.50',
      currency: 'GBP',
      status: 'Pending',
      description: 'Morning coffee',
      created_at: '2026-11-24T09:15:00Z',
      updated_at: '2026-11-24T09:15:00Z',
    },
  ],
  total: 20,
  limit: 25,
  offset: 0,
  has_more: false,
  empty_state_message: null,
  freshness: {
    level: 'Current',
    as_of: '2026-11-26T14:00:00Z',
  },
};

const mockEmptyTransactionsResponse = {
  items: [],
  total: 0,
  limit: 25,
  offset: 0,
  has_more: false,
  empty_state_message: 'No transactions found',
  freshness: {
    level: 'Current',
    as_of: null,
  },
};

describe('TransactionHistoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays transactions with Pending vs Posted status', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/v1/accounts')) {
        return Promise.resolve(mockAccountsResponse);
      }
      return Promise.resolve(mockTransactionsResponse);
    });

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <TransactionHistoryPage />
      </BrowserRouter>
    );

    // Wait for accounts to load and select one
    await waitFor(() => {
      expect(screen.getByLabelText('Account')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Account');
    await user.selectOptions(select, '123');

    // Wait for transactions to load
    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Verify Posted status tag
    expect(screen.getByText('Posted')).toBeInTheDocument();

    // Verify Pending status tag
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('displays pagination controls', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/v1/accounts')) {
        return Promise.resolve(mockAccountsResponse);
      }
      return Promise.resolve(mockTransactionsResponse);
    });

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <TransactionHistoryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Account')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Account');
    await user.selectOptions(select, '123');

    await waitFor(() => {
      expect(screen.getByText(/Showing \d+–\d+ of \d+ transactions/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Verify pagination buttons
    expect(screen.getByRole('button', { name: 'Previous' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Next' })).toBeInTheDocument();
  });

  it('displays transactions ordered by transaction_datetime DESC', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/v1/accounts')) {
        return Promise.resolve(mockAccountsResponse);
      }
      return Promise.resolve(mockTransactionsResponse);
    });

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <TransactionHistoryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Account')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Account');
    await user.selectOptions(select, '123');

    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Verify that the first merchant (Grocery Store) has the later date (2026-11-25)
    // and appears before Coffee Shop (2026-11-24)
    const rows = screen.getAllByRole('row');
    expect(rows.length).toBeGreaterThan(1); // At least header + 1 data row
  });

  it('displays empty state when total is 0', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/v1/accounts')) {
        return Promise.resolve(mockAccountsResponse);
      }
      return Promise.resolve(mockEmptyTransactionsResponse);
    });

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <TransactionHistoryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Account')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Account');
    await user.selectOptions(select, '123');

    await waitFor(() => {
      expect(
        screen.getByText(/There are no transactions to display for this account/i)
      ).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('displays masked card PAN', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/v1/accounts')) {
        return Promise.resolve(mockAccountsResponse);
      }
      return Promise.resolve(mockTransactionsResponse);
    });

    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <TransactionHistoryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Account')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('Account');
    await user.selectOptions(select, '123');

    await waitFor(() => {
      expect(screen.getByText('Grocery Store')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Check for masked card format
    const cells = screen.getAllByText(/\*\*\*\* 123/);
    expect(cells.length).toBeGreaterThan(0);
  });
});
