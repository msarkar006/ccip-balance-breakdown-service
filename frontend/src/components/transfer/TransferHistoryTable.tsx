import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  Tag,
  Stack,
} from '@carbon/react';
import { formatDateTime } from '../../lib/utils';
import type { BalanceTransfer, MoneyTransfer } from '../../types/transfer';

interface TransferHistoryTableProps {
  type: 'balance' | 'money';
  transfers: BalanceTransfer[] | MoneyTransfer[];
}

function getStatusTagKind(status: string): 'green' | 'blue' | 'red' | 'gray' {
  if (status === 'Completed') return 'green';
  if (status === 'Submitted' || status === 'Processing') return 'blue';
  if (status === 'Rejected' || status === 'Failed' || status === 'Blocked') return 'red';
  return 'gray';
}

function getGuidanceMessage(status: string, type: 'balance' | 'money'): string {
  if (type === 'balance') {
    if (status === 'Submitted') return 'We are checking this request. If you hear nothing within 5 working days, contact support.';
    if (status === 'ReviewRequired') return 'Review required. We will contact you if we need more information.';
    if (status === 'Rejected') return 'The amount was above your available credit. Request a smaller amount, or pay down your balance first.';
    if (status === 'Completed') return 'Transfer completed and added to your balance.';
  } else {
    if (status === 'Submitted') return 'Request received. Processing will begin shortly.';
    if (status === 'Processing') return 'Still processing. This usually completes within one working day.';
    if (status === 'Failed') return 'The transfer did not complete and no money was sent. You can try again, or contact support if it fails twice.';
    if (status === 'Rejected') return 'The amount was above your available credit at the time. Request a smaller amount.';
    if (status === 'Blocked') return 'This transfer was blocked by our security checks. Contact support for assistance.';
    if (status === 'Delayed') return 'Processing is taking longer than usual. We will notify you when it completes.';
    if (status === 'Completed') return 'Transfer completed successfully.';
  }
  return '';
}

function isBalanceTransfer(transfer: BalanceTransfer | MoneyTransfer): transfer is BalanceTransfer {
  return 'promotional_rate' in transfer;
}

export function TransferHistoryTable({ type, transfers }: TransferHistoryTableProps) {
  const headers =
    type === 'balance'
      ? ['Requested', 'Provider', 'Amount', 'Status and next step']
      : ['Requested', 'Payee', 'Amount', 'Fee', 'Status and next step'];

  const rows = transfers.map((transfer) => {
    const guidance = getGuidanceMessage(transfer.status, type);
    
    if (type === 'balance' && isBalanceTransfer(transfer)) {
      return {
        id: String(transfer.id),
        requested: formatDateTime(transfer.requested_on).split(',')[0],
        provider: transfer.external_transfer_id,
        amount: `£${parseFloat(transfer.transfer_amount).toFixed(2)}`,
        statusAndGuidance: (
          <Stack gap={2}>
            <Tag type={getStatusTagKind(transfer.status)} size="sm">
              {transfer.status}
            </Tag>
            <div className="cds--label-01">{guidance}</div>
          </Stack>
        ),
      };
    } else {
      const mtTransfer = transfer as MoneyTransfer;
      return {
        id: String(transfer.id),
        requested: formatDateTime(transfer.requested_on).split(',')[0],
        payee: mtTransfer.payee_name,
        amount: `£${parseFloat(mtTransfer.amount).toFixed(2)}`,
        fee: `£${(parseFloat(mtTransfer.amount) * 0.03).toFixed(2)}`,
        statusAndGuidance: (
          <Stack gap={2}>
            <Tag type={getStatusTagKind(transfer.status)} size="sm">
              {transfer.status}
            </Tag>
            <div className="cds--label-01">{guidance}</div>
          </Stack>
        ),
      };
    }
  });

  return (
    <DataTable rows={rows} headers={headers.map((h) => ({ key: h.toLowerCase().replace(/ /g, '_'), header: h }))}>
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
  );
}
