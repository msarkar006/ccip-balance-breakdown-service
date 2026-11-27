import { DataTable, Table, TableHead, TableRow, TableHeader, TableBody, TableCell, Tag, Button, InlineNotification } from '@carbon/react';
import { Renew } from '@carbon/icons-react';
import { useState } from 'react';
import { TrackerItem } from '../../types/tracker';
import { formatDateTime } from '../../lib/utils';
import { apiClient } from '../../lib/api-client';
import styles from './TrackerTable.module.scss';

interface TrackerTableProps {
  items: TrackerItem[];
  onRefresh: () => void;
}

export function TrackerTable({ items, onRefresh }: TrackerTableProps) {
  const [refreshing, setRefreshing] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [throttleMessage, setThrottleMessage] = useState('');

  const headers = [
    { key: 'type', header: 'Type' },
    { key: 'title', header: 'Title' },
    { key: 'status', header: 'Status' },
    { key: 'amount', header: 'Amount' },
    { key: 'updated', header: 'Last Updated' },
    { key: 'escalation', header: 'Escalation' },
    { key: 'action', header: 'Action' },
  ];

  const handleRefreshClick = async (item: TrackerItem) => {
    setRefreshing(`${item.entity_type}-${item.entity_id}`);
    setError('');
    setThrottleMessage('');

    try {
      const response = await apiClient.post<{ refresh_outcome: string; refresh_message: string }>(
        `/v1/status-tracker/${item.entity_type}/${item.entity_id}/refresh`,
        {}
      );

      if (response.refresh_outcome === 'unchanged') {
        setThrottleMessage(response.refresh_message);
      }

      onRefresh();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'status' in err && err.status === 429) {
        setThrottleMessage('Please wait before refreshing this item again');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to refresh status');
      }
    } finally {
      setRefreshing(null);
    }
  };

  const getStatusTagKind = (item: TrackerItem): 'green' | 'blue' | 'red' | 'gray' | 'purple' => {
    if (item.is_final && item.lifecycle_state.toLowerCase().includes('complete')) {
      return 'green';
    }
    if (item.lifecycle_state.toLowerCase().includes('fail') || item.lifecycle_state.toLowerCase().includes('reject')) {
      return 'red';
    }
    if (item.lifecycle_state.toLowerCase().includes('process') || item.lifecycle_state.toLowerCase().includes('submit')) {
      return 'blue';
    }
    if (item.lifecycle_state.toLowerCase().includes('blocked') || item.lifecycle_state.toLowerCase().includes('restrict')) {
      return 'purple';
    }
    return 'gray';
  };

  const rows = items.map((item) => ({
    id: `${item.entity_type}-${item.entity_id}`,
    type: item.entity_type,
    title: item.title,
    status: (
      <Tag type={getStatusTagKind(item)}>
        {item.status_label}
      </Tag>
    ),
    amount: item.amount || '-',
    updated: formatDateTime(item.last_updated_at),
    escalation: item.escalation?.is_escalated ? (
      <div>
        <Tag type="red">Escalated</Tag>
        <div className={`cds--label-01 ${styles.escalationGuidance}`}>{item.escalation.guidance}</div>
      </div>
    ) : (
      '-'
    ),
    action: (
      <Button
        kind="ghost"
        size="sm"
        renderIcon={Renew}
        onClick={() => handleRefreshClick(item)}
        disabled={refreshing === `${item.entity_type}-${item.entity_id}`}
      >
        {refreshing === `${item.entity_type}-${item.entity_id}` ? 'Refreshing...' : 'Refresh'}
      </Button>
    ),
  }));

  return (
    <>
      {error && (
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={error}
          lowContrast
          onCloseButtonClick={() => setError('')}
          className={styles.notification}
        />
      )}
      {throttleMessage && (
        <InlineNotification
          kind="info"
          title="Refresh throttled"
          subtitle={throttleMessage}
          lowContrast
          onCloseButtonClick={() => setThrottleMessage('')}
          className={styles.notification}
        />
      )}
      <DataTable rows={rows} headers={headers}>
        {({ rows, headers, getTableProps, getHeaderProps, getRowProps }) => (
          <Table {...getTableProps()}>
            <TableHead>
              <TableRow>
                {headers.map((header) => (
                  <TableHeader {...getHeaderProps({ header })} key={header.key}>
                    {header.header}
                  </TableHeader>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row) => (
                <TableRow {...getRowProps({ row })} key={row.id}>
                  {row.cells.map((cell) => (
                    <TableCell key={cell.id}>{cell.value}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </DataTable>
    </>
  );
}
