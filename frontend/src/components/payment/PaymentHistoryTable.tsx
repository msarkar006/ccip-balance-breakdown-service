import { DataTable, Table, TableHead, TableRow, TableHeader, TableBody, TableCell, Tag, Button, InlineNotification } from '@carbon/react';
import { useState } from 'react';
import { PaymentListItem } from '../../types/payment';
import { formatCurrency, formatDateTime } from '../../lib/utils';
import { apiClient } from '../../lib/api-client';
import { StepUpModal } from '../auth/StepUpModal';
import styles from './PaymentHistoryTable.module.scss';

interface PaymentHistoryTableProps {
  payments: PaymentListItem[];
  onRefresh: () => void;
}

const statusTagKinds: Record<string, 'green' | 'blue' | 'red' | 'gray'> = {
  Completed: 'green',
  Submitted: 'blue',
  Processing: 'blue',
  Failed: 'red',
  Cancelled: 'gray',
  Restricted: 'red',
};

export function PaymentHistoryTable({ payments, onRefresh }: PaymentHistoryTableProps) {
  const [cancellingPaymentId, setCancellingPaymentId] = useState<number | null>(null);
  const [showStepUpModal, setShowStepUpModal] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const headers = [
    { key: 'date', header: 'Date' },
    { key: 'type', header: 'Type' },
    { key: 'method', header: 'Method' },
    { key: 'amount', header: 'Amount' },
    { key: 'status', header: 'Status' },
    { key: 'action', header: 'Action' },
  ];

  const canCancel = (payment: PaymentListItem): boolean => {
    if (payment.status !== 'Submitted' && payment.status !== 'Processing') {
      return false;
    }
    if (payment.scheduled_date && new Date(payment.scheduled_date) > new Date()) {
      return true;
    }
    return payment.status === 'Submitted';
  };

  const handleCancelClick = (paymentId: number) => {
    setCancellingPaymentId(paymentId);
    setShowStepUpModal(true);
    setError('');
    setSuccessMessage('');
  };

  const handleStepUpSuccess = async (stepUpToken: string) => {
    if (!cancellingPaymentId) return;

    try {
      await apiClient.post(
        `/v1/payments/${cancellingPaymentId}/cancel`,
        {},
        { 'X-Step-Up-Proof': stepUpToken }
      );
      setSuccessMessage('Payment cancelled successfully');
      setCancellingPaymentId(null);
      onRefresh();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to cancel payment');
      }
    }
  };

  const rows = payments.map((payment) => ({
    id: payment.id.toString(),
    date: payment.scheduled_date ? formatDateTime(payment.scheduled_date) : formatDateTime(payment.created_at),
    type: payment.payment_type,
    method: payment.payment_method,
    amount: formatCurrency(parseFloat(payment.amount)),
    status: (
      <Tag type={statusTagKinds[payment.status] || 'gray'}>
        {payment.status}
      </Tag>
    ),
    action: canCancel(payment) ? (
      <Button
        kind="danger--tertiary"
        size="sm"
        onClick={() => handleCancelClick(payment.id)}
      >
        Cancel
      </Button>
    ) : (
      <span className={`cds--label-01 ${styles.actionCell}`}>None</span>
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
      {successMessage && (
        <InlineNotification
          kind="success"
          title="Success"
          subtitle={successMessage}
          lowContrast
          onCloseButtonClick={() => setSuccessMessage('')}
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

      <StepUpModal
        open={showStepUpModal}
        onClose={() => {
          setShowStepUpModal(false);
          setCancellingPaymentId(null);
        }}
        onSuccess={handleStepUpSuccess}
        scope="payment_cancel"
      />
    </>
  );
}
