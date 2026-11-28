import { useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Button, InlineLoading, InlineNotification } from '@carbon/react';
import { useAccount, useBalanceBreakdown, useBalanceBreakdowns } from '../lib/queries';
import { ErrorNotice } from '../components/common/ErrorNotice';
import { FreshnessBadge } from '../components/common/FreshnessBadge';
import { BreakdownTotals } from '../components/balance/BreakdownTotals';
import { CategoryList } from '../components/balance/CategoryList';
import { formatUtcDateTime } from '../lib/format';
import type { BalanceBreakdown } from '../types/account';
import '../components/balance/balance.css';

/** Lists the account's breakdowns (newest first) and shows the first in full. */
export default function BalanceBreakdownPage() {
  const { accountId } = useParams();
  const account = useAccount(accountId);
  const list = useBalanceBreakdowns(accountId, { limit: 1 });
  const firstId = list.data?.items[0]?.id;
  const detail = useBalanceBreakdown(firstId);
  const lastApproved = useRef<BalanceBreakdown | null>(null);
  if (detail.data) lastApproved.current = detail.data;

  const currency = account.data?.currency ?? 'GBP';
  const refreshFailed = detail.error !== null && lastApproved.current !== null;
  const shown = detail.data ?? (detail.error ? lastApproved.current : null);
  const error = list.error ?? (refreshFailed ? null : detail.error);
  const loading = list.loading || (firstId !== undefined && detail.loading && shown === null);

  let body;
  if (error) {
    body = <ErrorNotice error={error} title="Balance breakdown is unavailable" />;
  } else if (loading) {
    body = <InlineLoading status="active" description="Loading balance breakdown" role="status" />;
  } else if (!shown) {
    body = (
      <InlineNotification
        kind="info"
        lowContrast
        hideCloseButton
        title="No balance breakdown is available"
        subtitle="No dated breakdown is held for this account."
      />
    );
  } else {
    body = (
      <>
        {refreshFailed ? (
          <InlineNotification
            kind="warning"
            lowContrast
            hideCloseButton
            title="Could not refresh this breakdown"
            subtitle="The last approved values and their source time are shown unchanged, with the freshness state below. They are not described as current, final or real-time."
          />
        ) : null}
        <section className="balance-tile" aria-labelledby="asof-h">
          <h2 className="balance-tile__title" id="asof-h">
            Source time
          </h2>
          <p className="balance-timeline">
            <span>As of {shown.asOf ? <time dateTime={shown.asOf}>{formatUtcDateTime(shown.asOf)}</time> : 'not supplied'}</span>
            <FreshnessBadge freshness={{ ...shown.freshness, sourceTime: null }} />
          </p>
          <p className="balance-helper">
            This is the source as-of time, not the time the page was loaded. No maximum age has been approved, so this
            snapshot is not described as fresh, stale or real-time.
          </p>
          <Button kind="tertiary" size="sm" onClick={detail.reload}>
            Refresh breakdown
          </Button>
        </section>
        <BreakdownTotals breakdown={shown} currency={currency} />
        <h2 className="section-title">Balance categories</h2>
        <p className="balance-helper">
          Shown in the source display rank order (1 first). Each rate and date belongs to its own category.
        </p>
        <CategoryList categories={shown.categories} currency={currency} />
      </>
    );
  }

  return (
    <section aria-labelledby="page-heading">
      <h1 id="page-heading" className="page-title">
        Dated balance breakdown
      </h1>
      {shown ? (
        <p className="page-lead">
          Breakdown <span className="mono">{shown.sourceRef ?? shown.id}</span> for account{' '}
          <span className="mono">{account.data?.sourceRef ?? shown.accountId}</span>. This is a dated snapshot, not a live
          statement.
        </p>
      ) : null}
      {body}
    </section>
  );
}
