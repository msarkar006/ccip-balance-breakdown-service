import { useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Button, InlineLoading, InlineNotification, Pagination } from '@carbon/react';
import { useAccount, useApiQuery, usePayments } from '../lib/queries';
import { ErrorNotice } from '../components/common/ErrorNotice';
import { FreshnessBadge } from '../components/common/FreshnessBadge';
import { LabelledValue } from '../components/common/LabelledValue';
import { StatusTag } from '../components/common/StatusTag';
import { PaymentTable } from '../components/payment/PaymentTable';
import { formatDate, formatMoney } from '../lib/format';
import type { Payment, PaymentPage } from '../types/activity';
import '../components/payment/payment.css';

function PaymentDetail({ paymentId, currency }: { paymentId: string; currency: string }) {
  const detail = useApiQuery<Payment>(`/payments/${paymentId}`);
  if (detail.loading) return <InlineLoading status="active" description="Loading payment record" role="status" />;
  if (detail.error) return <ErrorNotice error={detail.error} title="Payment record is unavailable" />;
  const payment = detail.data;
  if (!payment) return null;
  return (
    <section className="pay-detail" aria-labelledby="pay-detail-h">
      <h2 className="pay-detail__title" id="pay-detail-h">
        Payment record {payment.sourceRef ?? payment.id}
      </h2>
      <dl className="pay-detail__dl">
        <LabelledValue label="Type (record)" value={<StatusTag status={`Type: ${payment.paymentType}`} />} />
        <LabelledValue label="Status (record)" value={<StatusTag status={`Status: ${payment.paymentStatus}`} />} />
        <LabelledValue label="Amount (record)" value={formatMoney(payment.paymentAmount, currency)} />
        <LabelledValue
          label="Payment date (record)"
          value={<time dateTime={payment.paymentDate}>{formatDate(payment.paymentDate)}</time>}
        />
        <LabelledValue label="Method (record)" value={payment.paymentMethod} />
        <LabelledValue label="Source bank (record)" value={payment.sourceBankName} />
        <LabelledValue label="Source account masked (record)" value={payment.sourceMaskedAccount} />
        <LabelledValue label="Mandate reference (record)" value={payment.viaMandateRef ?? 'None'} />
        <LabelledValue label="Freshness (record)" value={<FreshnessBadge freshness={payment.freshness} />} />
      </dl>
      <p className="pay-helper">{payment.informationalNotice}</p>
    </section>
  );
}

/** Payment history: source type, status and date verbatim, each with its informational notice. */
export default function PaymentListPage() {
  const { accountId } = useParams();
  const account = useAccount(accountId);
  const [paging, setPaging] = useState({ limit: 10, offset: 0 });
  const [detailId, setDetailId] = useState<string | null>(null);
  const list = usePayments(accountId, paging);
  const lastApproved = useRef<PaymentPage | null>(null);
  if (list.data) lastApproved.current = list.data;

  const currency = account.data?.currency ?? 'GBP';
  const refreshFailed = list.error !== null && lastApproved.current !== null;
  const shown = list.data ?? (list.error ? lastApproved.current : null);

  let body;
  if (list.error && !refreshFailed) {
    body = (
      <>
        <ErrorNotice error={list.error} title="Payment information is unavailable" />
        <p className="pay-helper">
          Nothing is estimated. See <Link to="/data-status">Data status and limitations</Link>.
        </p>
      </>
    );
  } else if (list.loading && shown === null) {
    body = <InlineLoading status="active" description="Loading payments" role="status" />;
  } else if (!shown || shown.items.length === 0) {
    body = <p>No payment records are held for this account in the prototype data.</p>;
  } else {
    const latest = shown.items[0].paymentDate;
    body = (
      <>
        {refreshFailed ? (
          <>
            <InlineNotification
              kind="warning"
              lowContrast
              hideCloseButton
              title="Could not refresh payment records"
              subtitle="The last approved records are shown with their source status and date unchanged. They are not described as current or final."
            />
            <p className="pay-timeline">
              <span>
                Latest source payment date shown: <time dateTime={latest}>{formatDate(latest)}</time> (a date, not a source
                timestamp)
              </span>
              <FreshnessBadge freshness={shown.items[0].freshness} />
            </p>
          </>
        ) : (
          <p className="pay-timeline">
            <span>
              Each record shows its own source payment date, which is a calendar date and not a timestamp. No source
              timestamp is supplied for these records.
            </span>
            <FreshnessBadge freshness={shown.items[0].freshness} />
          </p>
        )}
        <PaymentTable items={shown.items} currency={currency} onShowDetail={setDetailId} />
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
        <p className="pay-helper">
          Showing {shown.items.length} of {shown.total} payments for this account.
        </p>
        {detailId ? <PaymentDetail paymentId={detailId} currency={currency} /> : null}
      </>
    );
  }

  return (
    <section aria-labelledby="page-heading">
      <h1 id="page-heading" className="page-title">
        Payments
      </h1>
      <p className="page-lead">
        Existing payment records for account <span className="mono">{account.data?.sourceRef ?? accountId}</span>. These are
        records to read, not instructions.
      </p>
      <nav aria-label="Account information sections">
        <Link to={`/accounts/${accountId}/transactions`}>Transactions</Link>{' '}
        <Link to={`/accounts/${accountId}/payments`} aria-current="page">
          Payments
        </Link>{' '}
        <Link to="/data-status">Data status</Link>
      </nav>
      <InlineNotification
        kind="info"
        lowContrast
        hideCloseButton
        title="Information about existing records only"
        subtitle="This prototype cannot make, schedule, change or cancel a payment. A status such as Submitted or Completed is source information. It does not show that any action is possible, or that a payment is final."
      />
      <Button kind="tertiary" size="sm" onClick={list.reload}>
        Refresh payments
      </Button>
      {body}
    </section>
  );
}
