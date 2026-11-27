import { useEffect, useState } from 'react';
import { InlineNotification, Stack, Grid, Column, Tile } from '@carbon/react';
import { CategoryList } from '../components/balance/CategoryList';
import { AccountSelector } from '../components/account/AccountSelector';
import { BalanceBreakdownResponse } from '../types/balance';
import { apiClient } from '../lib/api-client';
import { formatCurrency, formatDateTime } from '../lib/utils';
import styles from './BalanceBreakdownPage.module.scss';

export function BalanceBreakdownPage() {
  const [breakdown, setBreakdown] = useState<BalanceBreakdownResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);

  useEffect(() => {
    // Fetch initial account list to get first account
    const fetchInitialAccount = async () => {
      try {
        const response = await apiClient.get<{ accounts: { id: number }[] }>('/v1/accounts');
        if (response.accounts && response.accounts.length > 0) {
          setSelectedAccountId(response.accounts[0].id);
        }
      } catch (error) {
        console.error('Failed to fetch accounts:', error);
        setError('Failed to load accounts');
      }
    };

    fetchInitialAccount();
  }, []);

  useEffect(() => {
    if (!selectedAccountId) return;

    const fetchBreakdown = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.get<BalanceBreakdownResponse>(
          `/v1/balance-breakdowns/current?account_id=${selectedAccountId}`
        );
        setBreakdown(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load balance breakdown');
      } finally {
        setLoading(false);
      }
    };

    fetchBreakdown();
  }, [selectedAccountId]);

  const showFreshnessIndicator = breakdown?.freshness.level === 'Current';
  const hasBalance = breakdown && parseFloat(breakdown.total_balance) > 0;

  return (
    <div className={styles.page}>
      <Stack gap={7}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>Balance breakdown</h1>
          </div>
          <AccountSelector
            selectedAccountId={selectedAccountId}
            onAccountChange={(accountId) => setSelectedAccountId(accountId)}
          />
        </div>

        {error && (
          <InlineNotification
            kind="error"
            title="Error"
            subtitle={error}
            lowContrast
            hideCloseButton
          />
        )}

        {loading && <div>Loading balance breakdown...</div>}

        {!loading && breakdown && (
          <>
            {showFreshnessIndicator && breakdown.freshness.as_of && (
              <InlineNotification
                kind="info"
                title="Up to date."
                subtitle={`Breakdown as of ${formatDateTime(breakdown.freshness.as_of)}.`}
                lowContrast
                hideCloseButton
              />
            )}

            <Grid>
              <Column lg={6} md={8} sm={4}>
                <Tile className={styles.totalTile}>
                  <Stack gap={3}>
                    <div className={styles.label}>Total outstanding</div>
                    <div className={styles.totalAmount}>
                      {formatCurrency(parseFloat(breakdown.total_balance))}
                    </div>
                  </Stack>
                </Tile>
              </Column>
              <Column lg={10} md={8} sm={4}>
                <Tile>
                  <Stack gap={3}>
                    <h2 className={styles.sectionTitle}>Pending, not yet in your balance</h2>
                    <div className={styles.pendingAmount}>
                      {formatCurrency(parseFloat(breakdown.pending_total))}
                    </div>
                    <p className={styles.helperText}>
                      Pending amounts are shown separately. They may change before they post, and are
                      not included in the total outstanding.
                    </p>
                  </Stack>
                </Tile>
              </Column>
            </Grid>

            {!hasBalance && (
              <Tile>
                <Stack gap={5}>
                  <h2 className={styles.sectionTitle}>You have no balance to pay</h2>
                  <p>
                    This account has a £0.00 balance, so there are no balance categories to show.
                    Anything pending is listed above and is not part of the balance yet.
                  </p>
                </Stack>
              </Tile>
            )}

            {hasBalance && (
              <section>
                <Stack gap={5}>
                  <h2 className={styles.sectionTitle}>What makes up your balance</h2>
                  <CategoryList categories={breakdown.categories} />
                </Stack>
              </section>
            )}
          </>
        )}
      </Stack>
    </div>
  );
}
