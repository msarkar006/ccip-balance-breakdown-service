import { render, screen } from '@testing-library/react';
import { FreshnessBadge } from '../components/common/FreshnessBadge';
import { LabelledValue } from '../components/common/LabelledValue';
import { ErrorNotice } from '../components/common/ErrorNotice';
import { StatusTag } from '../components/common/StatusTag';
import { Pagination } from '../components/common/Pagination';
import { ApiError } from '../lib/api-client';

describe('FreshnessBadge', () => {
  it.each(['freshness unavailable', 'unconfirmed freshness', 'stale'] as const)('prints %s verbatim', (state) => {
    render(<FreshnessBadge freshness={{ state, basis: 'test' }} />);
    expect(screen.getByText(state)).toBeInTheDocument();
  });

  it('prints the source time when supplied and omits it otherwise', () => {
    const { rerender } = render(
      <FreshnessBadge freshness={{ state: 'unconfirmed freshness', basis: 'b', sourceTime: '2026-11-22T14:05:00Z' }} />,
    );
    expect(screen.getByText('22 Nov 2026, 14:05 UTC')).toBeInTheDocument();
    rerender(<FreshnessBadge freshness={{ state: 'freshness unavailable', basis: 'b', sourceTime: null }} />);
    expect(screen.queryByText(/Source time/)).not.toBeInTheDocument();
  });
});

describe('LabelledValue', () => {
  it('shows Not supplied for null, undefined and empty, but keeps zero', () => {
    render(
      <dl>
        <LabelledValue label="A" value={null} />
        <LabelledValue label="B" value={undefined} />
        <LabelledValue label="C" value="" />
        <LabelledValue label="D" value="0.00" />
      </dl>,
    );
    expect(screen.getAllByText('Not supplied')).toHaveLength(3);
    expect(screen.getByText('0.00')).toBeInTheDocument();
  });
});

describe('StatusTag', () => {
  it('shows the status verbatim', () => {
    render(<StatusTag status="PendingActivation" />);
    expect(screen.getByText('PendingActivation')).toBeInTheDocument();
  });
});

describe('ErrorNotice', () => {
  it('renders ApiError.detail in an announced region', () => {
    render(<ErrorNotice error={new ApiError(404, 'Resource not found')} />);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Resource not found');
  });

  it('uses a safe generic message for unknown errors', () => {
    render(<ErrorNotice error={new Error('stack trace internals')} />);
    expect(screen.getByRole('alert')).not.toHaveTextContent('internals');
  });
});

describe('Pagination', () => {
  it('reports the visible range and total', () => {
    render(<Pagination total={23} limit={10} offset={10} onChange={() => undefined} />);
    expect(screen.getByText(/11.*20.*of 23/)).toBeInTheDocument();
  });
});
