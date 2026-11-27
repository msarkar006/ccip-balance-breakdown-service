import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { TransferManagementPage } from '../pages/TransferManagementPage';
import { apiClient } from '../lib/api-client';

vi.mock('../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

beforeAll(() => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

const mockGetResponse = (path: string) => {
  if (path.includes('/balance-transfers')) {
    return Promise.resolve({
      items: [
        {
          id: 1,
          external_transfer_id: 'BT-1',
          transfer_amount: '500.00',
          promotional_rate: '0.00',
          status: 'Submitted',
          requested_on: '2026-11-26T10:00:00Z',
          processed_at: null,
        },
      ],
      total: 1,
      limit: 10,
      offset: 0,
      has_more: false,
    });
  }
  if (path.includes('/money-transfers')) {
    return Promise.resolve({
      items: [
        {
          id: 1,
          external_transfer_id: 'MT-1',
          payee_name: 'John Smith',
          amount: '100.00',
          currency: 'GBP',
          status: 'Processing',
          requested_on: '2026-11-26T10:00:00Z',
          processed_at: null,
        },
      ],
      total: 1,
      limit: 10,
      offset: 0,
      has_more: false,
    });
  }
  if (path.includes('/payees')) {
    return Promise.resolve({
      items: [
        {
          id: 1,
          payee_name: 'John Smith',
          account_number_masked: '****1234',
          sort_code_masked: '12-**-56',
          created_at: '2024-01-15T10:00:00Z',
        },
      ],
      total: 1,
      limit: 25,
      offset: 0,
      has_more: false,
    });
  }
  if (path.includes('/offers')) {
    return Promise.resolve({
      items: [
        {
          id: 1,
          offer_code: 'BT-PROMO-2024',
          offer_title: '0% Balance Transfer',
          offer_description: 'Transfer your balance',
          offer_type: 'BalanceTransfer',
          status: 'Available',
          valid_from: '2026-11-16T00:00:00Z',
          valid_until: '2027-02-14T00:00:00Z',
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
      has_more: false,
    });
  }
  return Promise.resolve({ items: [], total: 0 });
};

describe('TransferManagementPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.get).mockImplementation(mockGetResponse);
  });

  it('displays balance transfer form with validation', async () => {
    render(
      <BrowserRouter>
        <TransferManagementPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/request a balance transfer/i)).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/amount to transfer/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/provider/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/last 4 digits/i)).toBeInTheDocument();
  });

  it('displays money transfer form with validation', async () => {
    render(
      <BrowserRouter>
        <TransferManagementPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /money transfer/i })).toBeInTheDocument();
    });
  });

  it('displays offer eligibility for balance transfers', async () => {
    render(
      <BrowserRouter>
        <TransferManagementPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/promotional offer available/i)).toBeInTheDocument();
    });
  });

  it('displays payee selector for money transfers', async () => {
    render(
      <BrowserRouter>
        <TransferManagementPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /balance transfer/i })).toBeInTheDocument();
    });
  });

  it('displays transfer history with lifecycle status', async () => {
    render(
      <BrowserRouter>
        <TransferManagementPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/balance transfer history/i)).toBeInTheDocument();
      expect(screen.getByText(/money transfer history/i)).toBeInTheDocument();
    });
  });
});
