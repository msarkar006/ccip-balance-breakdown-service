import { Tile } from '@carbon/react';
import { FreshnessBadge } from '../common/FreshnessBadge';
import { LabelledValue } from '../common/LabelledValue';
import { StatusTag } from '../common/StatusTag';
import { formatDate, formatMoney, formatPercent } from '../../lib/format';
import type { Account } from '../../types/account';
import './account.css';

/** The eight labelled account fields, each its own source field, with the freshness note. */
export function AccountSummary({ account }: { account: Account }) {
  const money = (value: string | null | undefined) => formatMoney(value, account.currency);
  const date = (value: string | null | undefined) => (value ? <time dateTime={value}>{formatDate(value)}</time> : null);
  const sourceTime = account.freshness.sourceTime;

  return (
    <Tile className="account-tile" aria-labelledby="acct-h">
      <div className="account-tile__head">
        <div>
          <h2 className="account-tile__title" id="acct-h">
            {account.productName}
          </h2>
          <p className="account-helper">
            Account <span className="mono">{account.sourceRef ?? account.id}</span> · Opened{' '}
            {account.openedOn ? <time dateTime={account.openedOn}>{formatDate(account.openedOn)}</time> : 'Not supplied'} ·
            Currency {account.currency}
          </p>
        </div>
        <StatusTag status={`Account status: ${account.accountStatus}`} />
      </div>
      <p className="account-helper">
        Account status is source context only. It does not show that any service is available.
      </p>
      <dl className="account-kvs">
        <LabelledValue label="Credit limit" value={money(account.creditLimit)} />
        <LabelledValue label="Available credit" value={money(account.availableCredit)} />
        <LabelledValue label="Current balance" value={money(account.currentBalance)} />
        <LabelledValue label="Statement balance" value={money(account.lastStatementBalance)} />
        <LabelledValue label="Minimum payment" value={money(account.minimumPayment)} />
        <LabelledValue label="Standard purchase APR" value={formatPercent(account.standardPurchaseApr)} />
        <LabelledValue label="Next statement date" value={date(account.nextStatementDate)} />
        <LabelledValue label="Payment due date" value={date(account.paymentDueDate)} />
      </dl>
      <p className="account-timeline">
        {sourceTime ? null : <span>Source timestamp for account fields: not supplied</span>}
        <FreshnessBadge freshness={account.freshness} />
      </p>
      <p className="account-helper">
        {sourceTime ? null : 'No source time is supplied for these account fields, so no currency of data is claimed. '}
        Statement and due dates are calendar dates, not timestamps.
      </p>
    </Tile>
  );
}

