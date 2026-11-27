import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { RewardsOffersPage } from '../pages/RewardsOffersPage';
import { apiClient } from '../lib/api-client';

vi.mock('../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
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

describe('RewardsOffersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays rewards programme summary with points', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      programme: {
        programme_name: 'NBS Everyday Rewards',
        points_balance: 3420,
        status: 'Active',
        as_of: '2026-11-26T06:00:00Z',
      },
      relevant_offers: [],
      freshness: {
        level: 'Current',
        as_of: '2026-11-26T06:00:00Z',
      },
    });

    render(
      <BrowserRouter>
        <RewardsOffersPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('NBS Everyday Rewards')).toBeInTheDocument();
      expect(screen.getByText(/3,420 points/i)).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
    });
  });

  it('displays relevant offers list', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      programme: null,
      relevant_offers: [
        {
          id: 1,
          offer_code: 'BT-PROMO-2024',
          offer_title: '0% balance transfer for 18 months',
          offer_description: 'Move a balance and pay 0% interest',
          offer_type: 'BalanceTransfer',
          status: 'Available',
          valid_from: '2026-11-16T00:00:00Z',
          valid_until: '2027-01-31T00:00:00Z',
        },
      ],
      freshness: {
        level: 'Current',
        as_of: '2026-11-26T06:00:00Z',
      },
    });

    render(
      <BrowserRouter>
        <RewardsOffersPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('0% balance transfer for 18 months')).toBeInTheDocument();
      expect(screen.getByText(/move a balance and pay 0% interest/i)).toBeInTheDocument();
    });
  });

  it('displays empty state when no programme and no offers', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      programme: null,
      relevant_offers: [],
      freshness: {
        level: 'Current',
        as_of: '2026-11-26T06:00:00Z',
      },
    });

    render(
      <BrowserRouter>
        <RewardsOffersPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Nothing to show for this account right now')).toBeInTheDocument();
      expect(screen.getByText(/no rewards programme and no offers available/i)).toBeInTheDocument();
    });
  });
});
