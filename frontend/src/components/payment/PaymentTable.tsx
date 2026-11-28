import { Button, DataTable, Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@carbon/react';
import { NOT_SUPPLIED } from '../common/LabelledValue';
import { StatusTag } from '../common/StatusTag';
import { formatDate, formatMoney } from '../../lib/format';
import type { Payment } from '../../types/activity';
import './payment.css';

const HEADERS = [
  { key: 'ref', header: 'Payment' },
  { key: 'type', header: 'Type' },
  { key: 'status', header: 'Status' },
  { key: 'amount', header: 'Amount' },
  { key: 'date', header: 'Payment date' },
  { key: 'method', header: 'Method' },
  { key: 'bank', header: 'Source bank' },
  { key: 'account', header: 'Source account (masked)' },
  { key: 'mandate', header: 'Mandate reference (source text)' },
  { key: 'notice', header: 'Information' },
  { key: 'detail', header: 'Record' },
];

interface PaymentTableProps {
  items: Payment[];
  currency: string;
  onShowDetail: (id: string) => void;
}

/** Read-only DataTable of payment records. Every row carries its `informationalNotice`; there is no control that acts on a payment. */
export function PaymentTable({ items, currency, onShowDetail }: PaymentTableProps) {
  const byId = new Map(items.map((item) => [item.id, item]));
  const rows = items.map((item) => ({ id: item.id }));
  return (
    <DataTable rows={rows} headers={HEADERS}>
      {({ rows: tableRows, headers, getTableProps, getHeaderProps, getRowProps }) => (
        <TableContainer title="Payment history" description="Each record shows its own source payment date, which is a calendar date and not a timestamp.">
          <Table {...getTableProps()} aria-label="Payment history">
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
                const payment = byId.get(row.id);
                if (!payment) return null;
                const { key, ...rowProps } = getRowProps({ row });
                const name = payment.sourceRef ?? payment.id;
                return (
                  <TableRow key={key} {...rowProps}>
                    <TableCell className="pay-mono">{name}</TableCell>
                    <TableCell>
                      <StatusTag status={`Type: ${payment.paymentType}`} />
                    </TableCell>
                    <TableCell>
                      <StatusTag status={`Status: ${payment.paymentStatus}`} />
                    </TableCell>
                    <TableCell>{formatMoney(payment.paymentAmount, currency) ?? NOT_SUPPLIED}</TableCell>
                    <TableCell>
                      <time dateTime={payment.paymentDate}>{formatDate(payment.paymentDate)}</time>
                    </TableCell>
                    <TableCell>{payment.paymentMethod}</TableCell>
                    <TableCell>{payment.sourceBankName ?? NOT_SUPPLIED}</TableCell>
                    <TableCell className="pay-mono">{payment.sourceMaskedAccount ?? NOT_SUPPLIED}</TableCell>
                    <TableCell className="pay-mono">{payment.viaMandateRef ?? 'None'}</TableCell>
                    <TableCell className="pay-notice">{payment.informationalNotice}</TableCell>
                    <TableCell>
                      <Button kind="ghost" size="sm" onClick={() => onShowDetail(payment.id)}>
                        View record {name}
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
