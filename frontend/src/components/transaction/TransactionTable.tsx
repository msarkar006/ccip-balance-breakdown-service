import { Button, DataTable, Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow, Tag } from '@carbon/react';
import { FreshnessBadge } from '../common/FreshnessBadge';
import { NOT_SUPPLIED } from '../common/LabelledValue';
import { StatusTag } from '../common/StatusTag';
import { formatDate, formatMoney, formatUtcDateTime, formatYesNo } from '../../lib/format';
import type { Transaction } from '../../types/activity';
import './transaction.css';

const HEADERS = [
  { key: 'merchant', header: 'Merchant' },
  { key: 'status', header: 'Status' },
  { key: 'amount', header: 'Amount' },
  { key: 'time', header: 'Transaction time' },
  { key: 'posted', header: 'Posted date' },
  { key: 'card', header: 'Card' },
  { key: 'mcc', header: 'Merchant category code' },
  { key: 'instalment', header: 'Instalment eligibility (source indicator)' },
  { key: 'ref', header: 'Reference' },
  { key: 'detail', header: 'Record' },
];

interface TransactionTableProps {
  items: Transaction[];
  currency: string;
  onShowDetail: (id: string) => void;
}

/** Read-only DataTable of transactions. Transaction time and posted date are separate columns. */
export function TransactionTable({ items, currency, onShowDetail }: TransactionTableProps) {
  const byId = new Map(items.map((item) => [item.id, item]));
  const rows = items.map((item) => ({ id: item.id }));
  return (
    <DataTable rows={rows} headers={HEADERS}>
      {({ rows: tableRows, headers, getTableProps, getHeaderProps, getRowProps }) => (
        <TableContainer title="Account transactions" description="Each record shows its source status and its own dates.">
          <Table {...getTableProps()} aria-label="Account transactions">
            <TableHead>
              <TableRow>
                {headers.map((header) => {
                  const { key, ...rest } = getHeaderProps({ header });
                  return (
                    <TableHeader key={key} {...rest}>
                      {header.header}
                    </TableHeader>
                  );
                })}
              </TableRow>
            </TableHead>
            <TableBody>
              {tableRows.map((row) => {
                const tx = byId.get(row.id);
                if (!tx) return null;
                const { key, ...rowProps } = getRowProps({ row });
                return (
                  <TableRow key={key} {...rowProps}>
                    <TableCell>{tx.merchantName ?? NOT_SUPPLIED}</TableCell>
                    <TableCell>
                      <StatusTag status={`Status: ${tx.transactionStatus}`} />
                    </TableCell>
                    <TableCell>{formatMoney(tx.transactionAmount, currency) ?? NOT_SUPPLIED}</TableCell>
                    <TableCell>
                      <time dateTime={tx.transactionTime}>{formatUtcDateTime(tx.transactionTime)}</time>{' '}
                      <FreshnessBadge freshness={{ ...tx.freshness, sourceTime: null }} />
                    </TableCell>
                    <TableCell>
                      {tx.postedDate ? <time dateTime={tx.postedDate}>{formatDate(tx.postedDate)}</time> : NOT_SUPPLIED}
                    </TableCell>
                    <TableCell className="tx-mono">{tx.maskedPan ?? NOT_SUPPLIED}</TableCell>
                    <TableCell className="tx-mono">{tx.merchantCategoryCode ?? NOT_SUPPLIED}</TableCell>
                    <TableCell>
                      {tx.eligibleForInstalment === true ? (
                        <Tag type="gray" size="md">
                          Yes
                        </Tag>
                      ) : (
                        (formatYesNo(tx.eligibleForInstalment) ?? NOT_SUPPLIED)
                      )}
                    </TableCell>
                    <TableCell className="tx-mono">{tx.sourceRef ?? NOT_SUPPLIED}</TableCell>
                    <TableCell>
                      <Button kind="ghost" size="sm" onClick={() => onShowDetail(tx.id)}>
                        View record {tx.sourceRef ?? ''}
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </DataTable>
  );
}
