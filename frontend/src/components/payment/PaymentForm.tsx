import { useState } from 'react';
import { TextInput, DatePicker, DatePickerInput, Button, RadioButtonGroup, RadioButton, InlineNotification } from '@carbon/react';
import { apiClient } from '../../lib/api-client';
import { PaymentInitiationResponse } from '../../types/payment';
import { StepUpModal } from '../auth/StepUpModal';
import styles from './PaymentForm.module.scss';

interface PaymentFormProps {
  accountId: number;
  minimumPayment: string;
  currentBalance: string;
  onSuccess: (payment: PaymentInitiationResponse) => void;
}

export function PaymentForm({ accountId, minimumPayment, currentBalance, onSuccess }: PaymentFormProps) {
  const [amountType, setAmountType] = useState('minimum');
  const [otherAmount, setOtherAmount] = useState('');
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().split('T')[0]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showStepUpModal, setShowStepUpModal] = useState(false);
  const [pendingPayment, setPendingPayment] = useState<{ amount: string; date: string } | null>(null);

  const minPaymentFloat = parseFloat(minimumPayment);
  const currentBalanceFloat = parseFloat(currentBalance);

  const validateAmount = (amount: number): string | null => {
    if (isNaN(amount) || amount <= 0) {
      return 'Please enter a valid amount greater than £0.00';
    }
    if (amount < 1) {
      return 'The minimum amount is £1.00';
    }
    if (amount > currentBalanceFloat) {
      return `Amount cannot exceed current balance of £${currentBalance}`;
    }
    return null;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    let amount: number;
    if (amountType === 'minimum') {
      amount = minPaymentFloat;
    } else if (amountType === 'balance') {
      amount = currentBalanceFloat;
    } else {
      amount = parseFloat(otherAmount.replace(/[£,]/g, ''));
      const validationError = validateAmount(amount);
      if (validationError) {
        setError(validationError);
        return;
      }
    }

    const today = new Date().toISOString().split('T')[0];
    if (!paymentDate || paymentDate < today) {
      setError('Please select today or a future date');
      return;
    }

    const maxDate = new Date();
    maxDate.setDate(maxDate.getDate() + 90);
    if (paymentDate > maxDate.toISOString().split('T')[0]) {
      setError('You can schedule payments up to 90 days ahead');
      return;
    }

    setPendingPayment({ amount: amount.toFixed(2), date: paymentDate });
    setShowStepUpModal(true);
  };

  const handleStepUpSuccess = async (stepUpToken: string) => {
    if (!pendingPayment) return;

    setIsLoading(true);
    setError('');

    try {
      const idempotencyKey = `payment-${accountId}-${Date.now()}-${Math.random()}`;
      const response = await apiClient.post<PaymentInitiationResponse>(
        '/v1/payments',
        {
          account_id: accountId,
          amount: pendingPayment.amount,
          currency: 'GBP',
          payment_method: 'BankTransfer',
          scheduled_date: pendingPayment.date !== new Date().toISOString().split('T')[0] ? pendingPayment.date : null,
          idempotency_key: idempotencyKey,
        },
        {
          'Idempotency-Key': idempotencyKey,
          'X-Step-Up-Proof': stepUpToken,
        }
      );

      onSuccess(response);
      setAmountType('minimum');
      setOtherAmount('');
      setPendingPayment(null);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Payment submission failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit} className={styles.form}>
        {error && (
          <InlineNotification
            kind="error"
            title="Error"
            subtitle={error}
            lowContrast
            hideCloseButton
            className={styles.notification}
          />
        )}
        <RadioButtonGroup
          legendText="Amount to pay"
          name="amount-type"
          valueSelected={amountType}
          onChange={(value: string | number | undefined) => {
            if (typeof value === 'string') {
              setAmountType(value);
            }
          }}
        >
          <RadioButton labelText={`Minimum payment (£${minimumPayment})`} value="minimum" id="amount-minimum" />
          <RadioButton labelText={`Current balance (£${currentBalance})`} value="balance" id="amount-balance" />
          <RadioButton labelText="Other amount" value="other" id="amount-other" />
        </RadioButtonGroup>

        {amountType === 'other' && (
          <TextInput
            id="other-amount"
            labelText="Other amount (£)"
            helperText={`Enter an amount from £1.00 up to £${currentBalance}`}
            value={otherAmount}
            onChange={(e) => setOtherAmount(e.target.value)}
            type="text"
            inputMode="decimal"
          />
        )}

        <DatePicker
          datePickerType="single"
          value={paymentDate}
          onChange={(dates) => {
            if (dates[0]) {
              setPaymentDate(dates[0].toISOString().split('T')[0]);
            }
          }}
        >
          <DatePickerInput
            id="payment-date"
            labelText="Payment date"
            placeholder="yyyy-mm-dd"
            helperText="Choose today for immediate payment or a future date to schedule"
          />
        </DatePicker>

        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Submitting...' : 'Review payment'}
        </Button>
      </form>

      <StepUpModal
        open={showStepUpModal}
        onClose={() => {
          setShowStepUpModal(false);
          setPendingPayment(null);
        }}
        onSuccess={handleStepUpSuccess}
        scope="payment"
      />
    </>
  );
}
