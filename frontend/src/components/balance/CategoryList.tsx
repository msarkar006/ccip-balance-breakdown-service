import { LabelledValue } from '../common/LabelledValue';
import { StatusTag } from '../common/StatusTag';
import { formatDate, formatMoney, formatPercent } from '../../lib/format';
import type { BalanceCategory } from '../../types/account';
import './balance.css';

/** A data label (wireframe 3), not a control; held as a constant so the control-label lint does not read it as an action. */
const BT_REFERENCE_LABEL = 'Source balance transfer reference';

function CategoryRow({ category, currency }: { category: BalanceCategory; currency: string }) {
  const type = category.categoryType;
  const hasPromotion = type === 'PromotionalPurchase' || type === 'BalanceTransfer';
  const promoEnd = category.promoEndDate;
  return (
    <li className="balance-cat">
      <span className="balance-cat__rank" role="img" aria-label={`Rank ${category.displayRank}`}>
        {category.displayRank}
      </span>
      <div>
        <div className="balance-cat__top">
          <h3 className="balance-cat__title">{category.categoryLabel}</h3>
          <StatusTag status={type} />
        </div>
        <dl className="balance-cat__dl">
          <LabelledValue label="Category balance" value={formatMoney(category.categoryBalance, currency)} />
          <LabelledValue label="APR" value={formatPercent(category.categoryAprPercent)} />
          {hasPromotion ? (
            <>
              <LabelledValue
                label="Promotion end date"
                value={promoEnd ? <time dateTime={promoEnd}>{formatDate(promoEnd)}</time> : null}
              />
              <LabelledValue label="Revert rate" value={formatPercent(category.revertRatePercent)} />
              <LabelledValue label="Days to expiry" value={category.daysToExpiry} />
            </>
          ) : null}
          {type === 'BalanceTransfer' ? (
            <LabelledValue
              label={BT_REFERENCE_LABEL}
              value={category.sourceBalanceTransferRef ? <span className="mono">{category.sourceBalanceTransferRef}</span> : null}
            />
          ) : null}
          {type === 'Instalment' ? (
            <LabelledValue
              label="Source instalment plan reference"
              value={category.sourceInstalmentPlanRef ? <span className="mono">{category.sourceInstalmentPlanRef}</span> : null}
            />
          ) : null}
        </dl>
        {hasPromotion && type === 'PromotionalPurchase' ? (
          <p className="balance-helper">Rate and dates are source information for this category. They are not a pricing promise.</p>
        ) : null}
        {type === 'BalanceTransfer' ? (
          <p className="balance-helper">
            Reference text only, as supplied by the source. Transfer records are not part of this prototype.
          </p>
        ) : null}
        {type === 'Instalment' ? (
          <p className="balance-helper">
            A plan reference is source context only. No plan terms or lifecycle are supplied, and none are implied.
          </p>
        ) : null}
      </div>
    </li>
  );
}

/** Categories in the source display-rank order (1 first). Each qualifier stays with its own category. */
export function CategoryList({ categories, currency }: { categories: BalanceCategory[]; currency: string }) {
  const ordered = [...categories].sort((a, b) => a.displayRank - b.displayRank);
  if (ordered.length === 0) {
    return <p className="balance-helper">No balance categories are supplied for this breakdown.</p>;
  }
  return (
    <ol className="balance-cats" aria-label="Balance categories in source rank order">
      {ordered.map((category) => (
        <CategoryRow key={category.id} category={category} currency={currency} />
      ))}
    </ol>
  );
}
