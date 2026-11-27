import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { TrackingActivityPage } from '../pages/TrackingActivityPage';
import { apiClient } from '../lib/api-client';

vi.mock('../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockTrackerData = {
  items: [
    {
      entity_type: 'Payment',
      entity_id: '1',
      title: 'Payment of £100.00',
      lifecycle_state: 'Processing',
      status_label: 'Processing',
      is_final: false,
      amount: '£100.00',
      last_updated_at: '2026-11-26T10:00:00Z',
      freshness: {
        level: 'Current',
        as_of: '2026-11-26T10:00:00Z',
      },
      escalation: null,
      guidance: {
        message_code: 'payment_processing',
        message: 'Your payment is being processed',
        next_step: 'Wait for confirmation',
      },
      resource_path: '/api/v1/payments/1',
    },
    {
      entity_type: 'MoneyTransfer',
      entity_id: '2',
      title: 'Money transfer of £50.00',
      lifecycle_state: 'Blocked',
      status_label: 'Blocked',
      is_final: false,
      amount: '£50.00',
      last_updated_at: '2026-11-25T15:00:00Z',
      freshness: {
        level: 'Current',
        as_of: '2026-11-25T15:00:00Z',
      },
      escalation: {
        is_escalated: true,
        reason: 'Transfer blocked for security review',
        guidance: 'Contact support for assistance',
      },
      guidance: {
        message_code: 'transfer_blocked',
        message: 'This transfer requires review',
        next_step: 'Contact support',
      },
      resource_path: '/api/v1/money-transfers/2',
    },
  ],
  total: 2,
  limit: 20,
  offset: 0,
  has_more: false,
  unresolved_count: 2,
  overall_message: null,
};

describe('TrackingActivityPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays tracker items with lifecycle states', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockTrackerData);

    render(
      <BrowserRouter>
        <TrackingActivityPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Activity Tracker')).toBeInTheDocument();
    });

    expect(screen.getByText('Payment of £100.00')).toBeInTheDocument();
    expect(screen.getByText('Money transfer of £50.00')).toBeInTheDocument();
    expect(screen.getByText('Processing')).toBeInTheDocument();
    expect(screen.getByText('Blocked')).toBeInTheDocument();
  });

  it('displays escalation cue when item is escalated', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockTrackerData);

    render(
      <BrowserRouter>
        <TrackingActivityPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Escalated')).toBeInTheDocument();
    });

    expect(screen.getByText('Contact support for assistance')).toBeInTheDocument();
  });

  it('filters to unresolved items when button clicked', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockTrackerData);

    render(
      <BrowserRouter>
        <TrackingActivityPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Activity Tracker')).toBeInTheDocument();
    });

    const unresolvedButton = screen.getByText(/Unresolved/);
    fireEvent.click(unresolvedButton);

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('status_group=unresolved')
      );
    });
  });

  it('displays empty state when no items', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      ...mockTrackerData,
      items: [],
      total: 0,
      unresolved_count: 0,
    });

    render(
      <BrowserRouter>
        <TrackingActivityPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No tracked items')).toBeInTheDocument();
    });

    expect(screen.getByText('You have no tracked items for this account')).toBeInTheDocument();
  });

  it('handles refresh button click with throttle message', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockTrackerData);
    vi.mocked(apiClient.post).mockResolvedValue({
      refresh_outcome: 'unchanged',
      refresh_message: 'No new information available',
    });

    render(
      <BrowserRouter>
        <TrackingActivityPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('Refresh')[0]).toBeInTheDocument();
    });

    const refreshButtons = screen.getAllByText('Refresh');
    fireEvent.click(refreshButtons[0]);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalled();
    });
  });
});
