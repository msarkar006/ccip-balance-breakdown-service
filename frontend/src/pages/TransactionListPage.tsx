import { useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Button, InlineLoading, InlineNotification, Pagination } from '@carbon/react';
import { useAccount, useApiQuery, useTransactions } from '../lib/queries';
import { ErrorNotice } from '../components/common/ErrorNotice';
import { FreshnessBadge } from '../components/common/FreshnessBadge';
import { LabelledValue } from '../components/common/LabelledValue';
import { StatusTag } from '../components/common/StatusTag';
import { TransactionTable } from '../components/transaction/TransactionTable';
import { formatDate, formatMoney, formatUtcDateTime, formatYesNo } from '../lib/format';
import type { Transaction, TransactionPage } from '../types/activity';
import '../components/transaction/transaction.css';

function TransactionDetail({ transactionId, currency }: { transactionId: string; currency: string }) {
  const detail = useApiQuery<Transaction>(`/transactions/${transactionId}`);
  if (detail.loading) return <InlineLoading status="active" description="Loading transaction record" role="status" />;
  if (detail.error) return <ErrorNotice error={detail.error} title="Transaction record is unavailable" />;
  const tx = detail.data;
  if (!tx) return null;
  return (
    <section className="tx-detail" aria-labelledby="tx-detail-h">
      <h2 className="tx-detail__title" id="tx-detail-h">
        Transaction record {tx.sourceRef ?? tx.id}
      </h2>
      <dl className="tx-detail__dl">
        <LabelledValue label="Merchant (record)" value={tx.merchantName} />
        <LabelledValue label="Status (record)" value={<StatusTag status={`Status: ${tx.transactionStatus}`} />} />
        <LabelledValue label="Amount (record)" value={formatMoney(tx.transactionAmount, currency)} />
        <LabelledValue
          label="Transaction time (record)"
          value={<time dateTime={tx.transactionTime}>{formatUtcDateTime(tx.transactionTime)}</time>}
        />
        <LabelledValue
          label="Posted date (record)"
          value={tx.postedDate ? <time dateTime={tx.postedDate}>{formatDate(tx.postedDate)}</time> : null}
        />
        <LabelledValue label="Card (record)" value={tx.maskedPan} />
        <LabelledValue label="Instalment eligibility (record)" value={formatYesNo(tx.eligibleForInstalment)} />
        <LabelledValue label="Freshness (record)" value={<FreshnessBadge freshness={tx.freshness} />} />
      </dl>
    </section>
  );
}

/** Account transactions: source status, separate transaction time and posted date, freshness label, paging. */
export default function TransactionListPage() {
  const { accountId } = useParams();
  const account = useAccount(accountId);
  const [paging, setPaging] = useState({ limit: 10, offset: 0 });
  const [detailId, setDetailId] = useState<string | null>(null);
  const list = useTransactions(accountId, paging);
  const lastApproved = useRef<TransactionPage | null>(null);
  if (list.data) lastApproved.current = list.data;

  const currency = account.data?.currency ?? 'GBP';
  const refreshFailed = list.error !== null && lastApproved.current !== null;
  const shown = list.data ?? (list.error ? lastApproved.current : null);

  let body;
  if (list.error && !refreshFailed) {
    body = (
      <>
        <ErrorNotice error={list.error} title="Transactions are unavailable" />
        <p className="tx-helper">
          Nothing is estimated. See <Link to="/data-status">Data status and limitations</Link>.
        </p>
      </>
    );
  } else if (list.loading && shown === null) {
    body = <InlineLoading status="active" description="Loading transactions" role="status" />;
  } else if (!shown || shown.items.length === 0) {
    body = <p>No transaction records are held for this account in the prototype data.</p>;
  } else {
    const newest = shown.items[0];
    body = (
      <>
        {refreshFailed ? (
          <>
            <InlineNotification
              kind="warning"
              lowContrast
              hideCloseButton
              title="Could not refresh transactions"
              subtitle="The last approved records are shown with their source status and dates unchanged. They are not described as current, posted or final."
            />
            <p className="tx-timeline">
              <span>
                Last approved source time:{' '}
                <time dateTime={newest.transactionTime}>{formatUtcDateTime(newest.transactionTime)}</time>
              </span>
              <FreshnessBadge freshness={{ ...newest.freshness, sourceTime: null }} />
            </p>
          </>
        ) : null}
        <TransactionTable items={shown.items} currency={currency} onShowDetail={setDetailId} />
        <Pagination
          page={Math.floor(shown.offset / shown.limit) + 1}
          pageSize={shown.limit}
          pageSizes={[10, 25, 50]}
          totalItems={shown.total}
          itemsPerPageText="Records per page"
          onChange={({ page, pageSize }: { page: number; pageSize: number }) =>
            setPaging({ limit: pageSize, offset: pageSize === shown.limit ? (page - 1) * pageSize : 0 })
          }
        />
        <p className="tx-helper">
          Showing {shown.items.length} of {shown.total} records for this account. Each transaction time is a source
          timestamp. No maximum age is approved, so it carries the label shown. A record without a source timestamp is
          labelled freshness unavailable.
        </p>
        {detailId ? <TransactionDetail transactionId={detailId} currency={currency} /> : null}
      </>
    );
  }

  return (
    <section aria-labelledby="page-heading">
      <h1 id="page-heading" className="page-title">
        Transactions
      </h1>
      <p className="page-lead">
        Transactions on account <span className="mono">{account.data?.sourceRef ?? accountId}</span>. Each record shows its
        source status and its own dates.
      </p>
      <nav className="tx-tabs" aria-label="Account information sections">
        <Link to={`/accounts/${accountId}/transactions`} aria-current="page">
          Transactions
        </Link>{' '}
        <Link to={`/accounts/${accountId}/payments`}>Payments</Link> <Link to="/data-status">Data status</Link>
      </nav>
      <InlineNotification
        kind="info"
        lowContrast
        hideCloseButton
        title="Pending is not posted"
        subtitle="A pending transaction has not been shown as posted by the source. This page does not describe any transaction as settled or final."
      />
      <Button kind="tertiary" size="sm" onClick={list.reload}>
        Refresh transactions
      </Button>
      {body}
    </section>
  );
}
