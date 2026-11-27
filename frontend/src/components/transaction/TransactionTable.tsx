import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  Tag,
  Button,
  Stack,
} from '@carbon/react';
import { Transaction } from '../../types/transaction';
import { formatCurrency, formatDateTime, formatDate } from '../../lib/utils';
import styles from './TransactionTable.module.scss';

interface TransactionTableProps {
  transactions: Transaction[];
  hasPrevious: boolean;
  hasNext: boolean;
  onPrevious: () => void;
  onNext: () => void;
  loading: boolean;
  total: number;
  offset: number;
  limit: number;
}

interface TransactionRow {
  id: string;
  merchant_name: string;
  amount: string;
  transaction_date: string;
  posting_date: string;
  status: string;
  statusKind: 'green' | 'blue' | 'gray';
  card: string;
}

export function TransactionTable({
  transactions,
  hasPrevious,
  hasNext,
  onPrevious,
  onNext,
  loading,
  total,
  offset,
  limit,
}: TransactionTableProps) {
  const headers = [
    { key: 'merchant_name', header: 'Merchant' },
    { key: 'amount', header: 'Amount' },
    { key: 'transaction_date', header: 'Transaction date' },
    { key: 'posting_date', header: 'Posted date' },
    { key: 'status', header: 'Status' },
    { key: 'card', header: 'Card' },
  ];

  const rows: TransactionRow[] = transactions.map((transaction) => {
    // Parse amount as number and handle sign (purchases positive, refunds negative)
    const amountValue = parseFloat(transaction.amount);
    const formattedAmount = formatCurrency(Math.abs(amountValue));
    
    // Determine status tag color
    let statusKind: 'green' | 'blue' | 'gray' = 'gray';
    if (transaction.status === 'Posted') {
      statusKind = 'green';
    } else if (transaction.status === 'Pending') {
      statusKind = 'blue';
    }

    // Extract last 4 digits from account_id for masked PAN
    // In a real app, this would come from a card number field
    const maskedCard = `**** ${String(transaction.account_id).slice(-4)}`;

    return {
      id: String(transaction.id),
      merchant_name: transaction.merchant_name,
      amount: formattedAmount,
      transaction_date: formatDateTime(transaction.transaction_date),
      posting_date: transaction.posting_date ? formatDate(transaction.posting_date) : '—',
      status: transaction.status,
      statusKind,
      card: maskedCard,
    };
  });

  const startIndex = offset + 1;
  const endIndex = Math.min(offset + limit, total);

  return (
    <Stack gap={5}>
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
              {rows.map((row) => {
                const typedRow = rows.find((r) => r.id === row.id) as unknown as TransactionRow | undefined;
                return (
                  <TableRow {...getRowProps({ row })} key={row.id}>
                    {row.cells.map((cell) => {
                      if (cell.info.header === 'status' && typedRow) {
                        return (
                          <TableCell key={cell.id}>
                            <Tag type={typedRow.statusKind}>{cell.value}</Tag>
                          </TableCell>
                        );
                      }
                      return <TableCell key={cell.id}>{cell.value}</TableCell>;
                    })}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </DataTable>

      <div className={styles.pagination}>
        <div className={styles.paginationInfo}>
          Showing {startIndex}–{endIndex} of {total} transactions
        </div>
        <div className={styles.paginationButtons}>
          <Button
            kind="tertiary"
            size="sm"
            onClick={onPrevious}
            disabled={!hasPrevious || loading}
          >
            Previous
          </Button>
          <Button
            kind="tertiary"
            size="sm"
            onClick={onNext}
            disabled={!hasNext || loading}
          >
            Next
          </Button>
        </div>
      </div>
    </Stack>
  );
}
