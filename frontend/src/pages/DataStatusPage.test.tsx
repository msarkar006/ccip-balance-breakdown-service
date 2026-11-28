import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import DataStatusPage from './DataStatusPage';
import { renderWithProviders } from '../test/render';

afterEach(() => vi.unstubAllGlobals());

describe('DataStatusPage', () => {
  it('explains the three labels and makes no network call', () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    renderWithProviders(<DataStatusPage />);
    expect(screen.getByRole('heading', { name: 'Data status and limitations', level: 1 })).toBeInTheDocument();
    const table = screen.getByRole('table', { name: 'Freshness labels and what they mean' });
    for (const label of ['freshness unavailable', 'unconfirmed freshness', 'stale']) {
      expect(within(table).getByText(label)).toBeInTheDocument();
    }
    expect(screen.getByText('At present no maximum age is approved, so a source timestamp is shown as unconfirmed freshness.')).toBeInTheDocument();
    expect(screen.getByText('Source information could not be refreshed')).toBeInTheDocument();
    expect(screen.getByText('Design notes for this wireframe')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
