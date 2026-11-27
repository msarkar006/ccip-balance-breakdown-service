import { AccountOverview } from '../../types/account';
import { formatCurrency, formatDate } from '../../lib/utils';
import styles from './CardStatus.module.scss';

interface CardStatusProps {
  overview: AccountOverview;
}

export function CardStatus({ overview }: CardStatusProps) {
  const cardDisplay = overview.cards.map((card) => 
    `${card.card_number_masked} · ${card.card_status}`
  ).join(', ') || 'No card information';

  return (
    <div className={styles.cardContainer}>
      <div className={styles.gridContainer}>
        <div>
          <div className={`cds--label-01 ${styles.fieldLabel}`}>
            Payment due date
          </div>
          <div className={`cds--type-heading-03 ${styles.fieldValueLarge}`}>
            {formatDate(overview.payment_due_date)}
          </div>
        </div>

        <div>
          <div className={`cds--label-01 ${styles.fieldLabel}`}>
            Minimum payment
          </div>
          <div className={`cds--type-heading-03 ${styles.fieldValueLarge}`}>
            {formatCurrency(parseFloat(overview.minimum_payment_due))}
          </div>
        </div>

        <div>
          <div className={`cds--label-01 ${styles.fieldLabel}`}>
            Account status
          </div>
          <div className={styles.fieldValue}>{overview.account_status}</div>
        </div>

        <div>
          <div className={`cds--label-01 ${styles.fieldLabel}`}>
            Card
          </div>
          <div className={styles.fieldValue}>{cardDisplay}</div>
        </div>
      </div>
    </div>
  );
}
