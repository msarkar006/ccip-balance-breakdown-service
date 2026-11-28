import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataRightsPage from './DataRightsPage';
import { jsonResponse, renderWithProviders } from '../test/render';

const existing = {
  id: '11111111-1111-1111-1111-111111111111',
  subjectRef: 'DRR-0001',
  requestType: 'export',
  status: 'received',
  requestedAt: '2026-11-25T10:00:00Z',
  dueAt: '2026-12-25T10:00:00Z',
  completedAt: null,
  outcomeSummary: null,
};
const page = (items: unknown[]) => ({ items, total: items.length, limit: 25, offset: 0 });

afterEach(() => vi.restoreAllMocks());

describe('DataRightsPage', () => {
  it('shows the empty state', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(page([])));
    renderWithProviders(<DataRightsPage />);
    expect(await screen.findByText('You have not made any data rights requests.')).toBeInTheDocument();
  });

  it('lists requests with status and Not yet for completion', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(page([existing])));
    renderWithProviders(<DataRightsPage />);
    expect(await screen.findByText('Status: Received')).toBeInTheDocument();
    expect(screen.getByText('Not yet')).toBeInTheDocument();
  });

  it('requires a request type before submitting', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(page([])));
    renderWithProviders(<DataRightsPage />);
    await screen.findByText('You have not made any data rights requests.');
    await userEvent.click(screen.getByRole('button', { name: 'Submit request' }));
    expect(await screen.findByText('Choose a request type.')).toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'POST')).toHaveLength(0);
  });

  it('posts with an Idempotency-Key and confirms', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) =>
      Promise.resolve(init?.method === 'POST' ? jsonResponse(existing, 201) : jsonResponse(page([existing]))),
    );
    renderWithProviders(<DataRightsPage />);
    await userEvent.selectOptions(screen.getByLabelText('Request type'), 'export');
    await userEvent.click(screen.getByRole('button', { name: 'Submit request' }));
    expect(await screen.findByText('Request received')).toBeInTheDocument();
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST');
    expect(post).toBeDefined();
    const headers = post?.[1]?.headers as Record<string, string>;
    expect(headers['Idempotency-Key']).toBeTruthy();
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({ requestType: 'export' });
  });

  it('shows the API detail when the request is not recorded', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) =>
      Promise.resolve(init?.method === 'POST' ? jsonResponse({ detail: 'Internal server error' }, 500) : jsonResponse(page([]))),
    );
    renderWithProviders(<DataRightsPage />);
    await userEvent.selectOptions(screen.getByLabelText('Request type'), 'deletion');
    await userEvent.click(screen.getByRole('button', { name: 'Submit request' }));
    expect(await screen.findByText('Internal server error')).toBeInTheDocument();
    expect(screen.getByText('Request not recorded')).toBeInTheDocument();
  });
});
