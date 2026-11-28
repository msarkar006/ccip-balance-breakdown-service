import { Tile } from '@carbon/react';
import { LabelledValue } from '../common/LabelledValue';
import { formatMoney, formatYesNo } from '../../lib/format';
import type { BalanceBreakdown } from '../../types/account';
import './balance.css';

/** Totals as stored. Pending total is its own field; nothing is netted, summed or relabelled. */
export function BreakdownTotals({ breakdown, currency }: { breakdown: BalanceBreakdown; currency: string }) {
  const money = (value: string | null | undefined) => formatMoney(value, currency);
  return (
    <Tile className="balance-tile" aria-labelledby="tot-h">
      <h2 className="balance-tile__title" id="tot-h">
        Totals in this breakdown
      </h2>
      <dl className="balance-kvs">
        <LabelledValue label="Total outstanding" value={money(breakdown.totalOutstanding)} />
        <LabelledValue label="Pending total" value={money(breakdown.pendingTotal)} />
        <LabelledValue label="Purchases subtotal" value={money(breakdown.purchasesSubtotal)} />
        <LabelledValue label="Balance transfers subtotal" value={money(breakdown.balanceTransfersSubtotal)} />
        <LabelledValue label="Zero balance (source field)" value={formatYesNo(breakdown.isZeroBalance)} />
      </dl>
      <p className="balance-helper">
        {breakdown.isZeroBalance === true
          ? 'Zero balance does not remove the pending total. Both values stay visible. No statement is made that nothing is pending.'
          : 'Pending total is shown separately. It is not described as posted or settled. These values are not the same as current balance, statement balance, available credit or minimum payment on the account overview.'}
      </p>
    </Tile>
  );
}
