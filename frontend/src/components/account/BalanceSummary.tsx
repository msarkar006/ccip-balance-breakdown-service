import { Button, Stack, Grid, Column } from '@carbon/react';
import { AccountOverview } from '../../types/account';
import { formatCurrency } from '../../lib/utils';
import styles from './BalanceSummary.module.scss';

interface BalanceSummaryProps {
  overview: AccountOverview;
}

export function BalanceSummary({ overview }: BalanceSummaryProps) {
  const creditUsed = parseFloat(overview.current_balance);
  const creditLimit = parseFloat(overview.credit_limit);
  const usagePercentage = (creditUsed / creditLimit) * 100;

  return (
    <div className={styles.balanceContainer}>
      <Stack gap={5}>
        <div>
          <div className={`cds--label-01 ${styles.balanceLabel}`}>
            Current balance
          </div>
          <div className={`cds--type-heading-05 ${styles.balanceAmount}`}>
            {formatCurrency(parseFloat(overview.current_balance))}
          </div>
        </div>

        <div>
          <div className={`cds--label-01 ${styles.creditLabel}`}>
            Available credit <strong>{formatCurrency(parseFloat(overview.available_credit))}</strong> of{' '}
            <span>{formatCurrency(parseFloat(overview.credit_limit))}</span> credit limit
          </div>
          <progress
            value={creditUsed}
            max={creditLimit}
            aria-label="Credit used compared with credit limit"
            className={styles.progressBar}
          >
            {usagePercentage.toFixed(1)}%
          </progress>
        </div>

        <Grid narrow className={styles.buttonRow}>
          <Column sm={4} md={4} lg={8}>
            <Button>Make a payment</Button>
          </Column>
          <Column sm={4} md={4} lg={8}>
            <Button kind="tertiary">View balance breakdown</Button>
          </Column>
        </Grid>
      </Stack>
    </div>
  );
}
