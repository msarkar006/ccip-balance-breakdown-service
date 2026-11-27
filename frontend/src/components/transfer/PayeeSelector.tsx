import { Select, SelectItem } from '@carbon/react';
import type { Payee } from '../../types/transfer';

interface PayeeSelectorProps {
  payees: Payee[];
  selectedPayeeId: number;
  onChange: (payeeId: number) => void;
}

export function PayeeSelector({ payees, selectedPayeeId, onChange }: PayeeSelectorProps) {
  return (
    <Select
      id="payee"
      labelText="Pay to"
      value={String(selectedPayeeId)}
      onChange={(e) => onChange(Number(e.target.value))}
    >
      {payees.map((payee) => (
        <SelectItem
          key={payee.id}
          value={String(payee.id)}
          text={`${payee.payee_name} · ${payee.sort_code_masked} · ${payee.account_number_masked}`}
        />
      ))}
    </Select>
  );
}
