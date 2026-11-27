import { useEffect, useState } from 'react';
import { InlineNotification, Stack } from '@carbon/react';
import { TransactionTable } from '../components/transaction/TransactionTable';
import { AccountSelector } from '../components/account/AccountSelector';
import { TransactionListResponse } from '../types/transaction';
import { apiClient } from '../lib/api-client';
import styles from './TransactionHistoryPage.module.scss';

const PAGE_SIZE = 25;

export function TransactionHistoryPage() {
  const [data, setData] = useState<TransactionListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [offset, setOffset] = useState(0);

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

    const fetchTransactions = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await apiClient.get<TransactionListResponse>(
          `/v1/transactions?account_id=${selectedAccountId}&limit=${PAGE_SIZE}&offset=${offset}`
        );

        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load transactions');
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [selectedAccountId, offset]);

  const handlePrevious = () => {
    setOffset(Math.max(0, offset - PAGE_SIZE));
  };

  const handleNext = () => {
    setOffset(offset + PAGE_SIZE);
  };

  const hasTransactions = data && data.items.length > 0;
  const showEmptyState = !loading && data && data.total === 0;
  const hasPrevious = offset > 0;
  const hasNext = data?.has_more ?? false;

  return (
    <div className={styles.page}>
      <Stack gap={7}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>Transaction history</h1>
          </div>
          <AccountSelector
            selectedAccountId={selectedAccountId}
            onAccountChange={(accountId) => {
              setSelectedAccountId(accountId);
              setOffset(0);
            }}
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

        {loading && <div>Loading transactions...</div>}

        {showEmptyState && (
          <InlineNotification
            kind="info"
            title="No transactions"
            subtitle="There are no transactions to display for this account."
            lowContrast
            hideCloseButton
          />
        )}

        {hasTransactions && (
          <TransactionTable
            transactions={data.items}
            hasPrevious={hasPrevious}
            hasNext={hasNext}
            onPrevious={handlePrevious}
            onNext={handleNext}
            loading={loading}
            total={data.total}
            offset={offset}
            limit={PAGE_SIZE}
          />
        )}
      </Stack>
    </div>
  );
}
