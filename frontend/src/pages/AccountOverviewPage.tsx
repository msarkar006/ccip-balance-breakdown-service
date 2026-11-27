import { useState, useEffect } from 'react';
import { Grid, Column, Stack, InlineNotification } from '@carbon/react';
import { AccountSelector } from '../components/account/AccountSelector';
import { BalanceSummary } from '../components/account/BalanceSummary';
import { CardStatus } from '../components/account/CardStatus';
import { AccountOverview } from '../types/account';
import { apiClient } from '../lib/api-client';
import { formatDateTime } from '../lib/utils';
import styles from './AccountOverviewPage.module.scss';

export function AccountOverviewPage() {
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [overview, setOverview] = useState<AccountOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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
      } finally {
        setLoading(false);
      }
    };

    fetchInitialAccount();
  }, []);

  useEffect(() => {
    if (!selectedAccountId) return;

    const fetchOverview = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await apiClient.get<AccountOverview>(`/v1/accounts/${selectedAccountId}/overview`);
        setOverview(data);
        
        // Update session selected account
        await apiClient.put('/v1/accounts/selection', { account_id: selectedAccountId });
      } catch (error) {
        setError('We could not switch account. You are still viewing the previous account. Try again in a moment, or contact support if this keeps happening.');
        console.error('Failed to fetch overview:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOverview();
  }, [selectedAccountId]);

  const handleAccountChange = async (accountId: number) => {
    setSelectedAccountId(accountId);
  };

  return (
    <div>
      <Grid>
        <Column sm={4} md={8} lg={16}>
          <div className={styles.pageHeader}>
            <div>
              <h1 className="cds--type-heading-04">Account overview</h1>
              {overview && (
                <p className={`cds--label-01 ${styles.cardSubtitle}`}>
                  {overview.cards[0]?.card_type || 'Credit Card'} · card {overview.cards[0]?.card_number_masked || ''}
                </p>
              )}
            </div>
            <div className={styles.accountSelectorContainer}>
              <AccountSelector
                selectedAccountId={selectedAccountId}
                onAccountChange={handleAccountChange}
              />
            </div>
          </div>

          {error && (
            <div className={styles.errorContainer}>
              <InlineNotification
                kind="error"
                title="We could not switch account"
                subtitle={error}
                hideCloseButton
                lowContrast
              />
            </div>
          )}

          {loading && !overview && (
            <div>Loading account information...</div>
          )}

          {overview && (
            <Stack gap={7}>
              <section aria-labelledby="summaryHeading" className={styles.sectionContainer}>
                <h2 id="summaryHeading" className="cds--visually-hidden">
                  Balance and payment summary
                </h2>
                <Grid narrow>
                  <Column sm={4} md={8} lg={6}>
                    <BalanceSummary overview={overview} />
                  </Column>
                  <Column sm={4} md={8} lg={10}>
                    <CardStatus overview={overview} />
                  </Column>
                </Grid>
                {overview.show_as_of_cue && overview.as_of && (
                  <div className={styles.sectionContainer}>
                    <InlineNotification
                      kind="info"
                      title="Up to date."
                      subtitle={`Figures as of ${formatDateTime(overview.as_of)}`}
                      hideCloseButton
                      lowContrast
                    />
                  </div>
                )}
              </section>

              <section aria-labelledby="txHeading">
                <h2 id="txHeading" className="cds--type-heading-03">
                  Recent transactions
                </h2>
                <div className={styles.placeholderTile}>
                  <p>Transaction list will be implemented in future tasks.</p>
                </div>
              </section>
            </Stack>
          )}
        </Column>
      </Grid>
    </div>
  );
}
