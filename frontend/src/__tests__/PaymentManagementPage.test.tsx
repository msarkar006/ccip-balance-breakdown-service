import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { PaymentManagementPage } from '../pages/PaymentManagementPage';
import { apiClient } from '../lib/api-client';

vi.mock('../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockGuidance = {
  minimum_payment: '121.56',
  due_date: '2026-12-15T00:00:00Z',
  current_balance: '4862.35',
  max_payment_amount: '4862.35',
  direct_debit_coverage: {
    coverage_status: 'expected_to_cover',
    manual_payment_may_be_required: false,
    reason: 'Active MinimumPayment mandate with recent collection',
  },
};

const mockPayments = {
  items: [
    {
      id: 1,
      account_id: 1,
      external_payment_id: 'PMT-1',
      idempotency_key: null,
      payment_type: 'OneOff',
      payment_method: 'BankTransfer',
      amount: '100.00',
      currency: 'GBP',
      status: 'Completed',
      scheduled_date: null,
      processed_at: '2026-11-16T10:00:00Z',
      created_at: '2026-11-15T14:00:00Z',
      updated_at: '2026-11-16T10:00:00Z',
    },
    {
      id: 2,
      account_id: 1,
      external_payment_id: 'PMT-2',
      idempotency_key: null,
      payment_type: 'Scheduled',
      payment_method: 'BankTransfer',
      amount: '150.00',
      currency: 'GBP',
      status: 'Submitted',
      scheduled_date: '2026-12-01T00:00:00Z',
      processed_at: null,
      created_at: '2026-11-15T14:00:00Z',
      updated_at: '2026-11-15T14:00:00Z',
    },
  ],
  total: 2,
  limit: 20,
  offset: 0,
  has_more: false,
  empty_state_message: null,
  freshness: {
    level: 'Current',
    as_of: null,
  },
};

describe('PaymentManagementPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays payment guidance and form', async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path.includes('/guidance')) {
        return Promise.resolve(mockGuidance);
      }
      if (path.includes('/payments')) {
        return Promise.resolve(mockPayments);
      }
      return Promise.reject(new Error('Unknown path'));
    });

    render(
      <BrowserRouter>
        <PaymentManagementPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Payment Management')).toBeInTheDocument();
    });

    expect(screen.getByText('Make a payment')).toBeInTheDocument();
    expect(screen.getByText('£121.56')).toBeInTheDocument();
    expect(screen.getByText(/15\/12\/2026/)).toBeInTheDocument();
  });

  it('displays payment history with status tags', async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path.includes('/guidance')) {
        return Promise.resolve(mockGuidance);
      }
      if (path.includes('/payments')) {
        return Promise.resolve(mockPayments);
      }
      return Promise.reject(new Error('Unknown path'));
    });

    render(
      <BrowserRouter>
        <PaymentManagementPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Payment history')).toBeInTheDocument();
    });

    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Submitted')).toBeInTheDocument();
  });

  it('displays direct debit coverage message when expected to cover', async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path.includes('/guidance')) {
        return Promise.resolve(mockGuidance);
      }
      if (path.includes('/payments')) {
        return Promise.resolve(mockPayments);
      }
      return Promise.reject(new Error('Unknown path'));
    });

    render(
      <BrowserRouter>
        <PaymentManagementPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Direct debit will cover minimum payment')).toBeInTheDocument();
    });

    expect(screen.getByText(/Active MinimumPayment mandate/)).toBeInTheDocument();
  });

  it('displays warning when direct debit not expected to cover', async () => {
    const guidanceWithWarning = {
      ...mockGuidance,
      direct_debit_coverage: {
        coverage_status: 'not_expected_to_cover',
        manual_payment_may_be_required: true,
        reason: 'Fixed amount £50 is less than minimum payment',
      },
    };

    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path.includes('/guidance')) {
        return Promise.resolve(guidanceWithWarning);
      }
      if (path.includes('/payments')) {
        return Promise.resolve(mockPayments);
      }
      return Promise.reject(new Error('Unknown path'));
    });

    render(
      <BrowserRouter>
        <PaymentManagementPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Direct debit may not cover full minimum payment')).toBeInTheDocument();
    });

    expect(screen.getByText(/You may need to make a manual payment/)).toBeInTheDocument();
  });

  it('displays empty state when no payment history', async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path.includes('/guidance')) {
        return Promise.resolve(mockGuidance);
      }
      if (path.includes('/payments')) {
        return Promise.resolve({ ...mockPayments, items: [], total: 0 });
      }
      return Promise.reject(new Error('Unknown path'));
    });

    render(
      <BrowserRouter>
        <PaymentManagementPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No payments found')).toBeInTheDocument();
    });

    expect(screen.getByText('You have no payment history for this account')).toBeInTheDocument();
  });
});
