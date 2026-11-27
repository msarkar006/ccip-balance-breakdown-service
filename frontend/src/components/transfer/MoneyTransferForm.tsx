import { useState, FormEvent } from 'react';
import { Button, TextInput, Select, SelectItem, Stack } from '@carbon/react';
import type { Payee } from '../../types/transfer';

interface MoneyTransferFormProps {
  availableCredit: number;
  payees: Payee[];
  onSubmit: (data: { payeeId: number; amount: string }) => Promise<void>;
}

export function MoneyTransferForm({
  availableCredit,
  payees,
  onSubmit,
}: MoneyTransferFormProps) {
  const [payeeId, setPayeeId] = useState(payees.length > 0 ? payees[0].id : 0);
  const [amount, setAmount] = useState('1200.00');
  const [amountError, setAmountError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const calculateFee = (val: string): number => {
    const num = parseFloat(val.replace(/[£,]/g, ''));
    return isNaN(num) ? 0 : num * 0.03;
  };

  const validateAmount = (val: string): string => {
    const num = parseFloat(val.replace(/[£,]/g, ''));
    if (isNaN(num)) return 'Enter an amount in pounds and pence, for example 500.00';
    if (num < 1) return 'The amount must be at least £1.00';
    const totalWithFee = num + calculateFee(val);
    if (totalWithFee > availableCredit) return `The amount plus fee (£${totalWithFee.toFixed(2)}) is more than your available credit of £${availableCredit.toFixed(2)}`;
    return '';
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    const amtErr = validateAmount(amount);
    setAmountError(amtErr);
    
    if (amtErr) {
      return;
    }
    
    setIsSubmitting(true);
    try {
      await onSubmit({ payeeId, amount });
      setAmount('');
    } catch {
      // Error handled by parent
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Stack gap={5}>
        <Select
          id="payee"
          labelText="Pay to"
          value={String(payeeId)}
          onChange={(e) => setPayeeId(Number(e.target.value))}
        >
          {payees.map((payee) => (
            <SelectItem
              key={payee.id}
              value={String(payee.id)}
              text={`${payee.payee_name} · ${payee.sort_code_masked} · ${payee.account_number_masked}`}
            />
          ))}
        </Select>
        
        <TextInput
          id="mtAmt"
          labelText="Amount (£)"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          invalid={!!amountError}
          invalidText={amountError}
          helperText={`Up to your available credit of £${availableCredit.toFixed(2)}. Fee on £${amount}: £${calculateFee(amount).toFixed(2)}`}
        />
        
        <div>
          <Button type="submit" disabled={isSubmitting || payees.length === 0}>
            {isSubmitting ? 'Processing...' : 'Review money transfer'}
          </Button>
        </div>
      </Stack>
    </form>
  );
}
