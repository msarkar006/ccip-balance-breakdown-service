import { useState, useEffect } from 'react';
import { Stack, Heading, InlineNotification, Button, ButtonSet } from '@carbon/react';
import { apiClient } from '../lib/api-client';
import { TrackerListResponse } from '../types/tracker';
import { TrackerTable } from '../components/tracker/TrackerTable';
import styles from './TrackingActivityPage.module.scss';

export function TrackingActivityPage() {
  const [trackerData, setTrackerData] = useState<TrackerListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterUnresolved, setFilterUnresolved] = useState(false);
  const accountId = 1; // TODO: Get from selected account context

  const fetchData = async () => {
    setIsLoading(true);
    setError('');

    try {
      const params = new URLSearchParams({
        account_id: accountId.toString(),
        limit: '20',
        offset: '0',
      });

      if (filterUnresolved) {
        params.append('status_group', 'unresolved');
      }

      const data = await apiClient.get<TrackerListResponse>(`/v1/status-tracker?${params}`);
      setTrackerData(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load tracker data');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterUnresolved]);

  if (isLoading) {
    return (
      <div>
        <Heading>Activity Tracker</Heading>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Stack gap={7}>
      <div>
        <Heading>Activity Tracker</Heading>
        <p className={`cds--label-01 ${styles.pageSubtitle}`}>
          Account ACC-1001 · Track payments, transfers, and status updates
        </p>
      </div>

      {error && (
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={error}
          lowContrast
          onCloseButtonClick={() => setError('')}
        />
      )}

      {trackerData?.overall_message && (
        <InlineNotification
          kind="warning"
          title="Attention required"
          subtitle={trackerData.overall_message}
          lowContrast
          hideCloseButton
        />
      )}

      <ButtonSet>
        <Button
          kind={!filterUnresolved ? 'primary' : 'tertiary'}
          onClick={() => setFilterUnresolved(false)}
        >
          All items ({trackerData?.total || 0})
        </Button>
        <Button
          kind={filterUnresolved ? 'primary' : 'tertiary'}
          onClick={() => setFilterUnresolved(true)}
        >
          Unresolved ({trackerData?.unresolved_count || 0})
        </Button>
      </ButtonSet>

      {trackerData && trackerData.items.length > 0 ? (
        <TrackerTable items={trackerData.items} onRefresh={fetchData} />
      ) : (
        <InlineNotification
          kind="info"
          title={filterUnresolved ? 'No unresolved items' : 'No tracked items'}
          subtitle={
            filterUnresolved
              ? 'All your payments and transfers are in a final state'
              : 'You have no tracked items for this account'
          }
          lowContrast
          hideCloseButton
        />
      )}
    </Stack>
  );
}
