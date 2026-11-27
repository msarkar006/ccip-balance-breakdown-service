import { useState, FormEvent } from 'react';
import { Button, TextInput, InlineNotification, Stack } from '@carbon/react';
import type { Offer } from '../../types/transfer';

interface BalanceTransferFormProps {
  availableCredit: number;
  offers: Offer[];
  onSubmit: (data: {
    amount: string;
    provider: string;
    last4: string;
    offerCode: string;
  }) => Promise<void>;
}

export function BalanceTransferForm({
  availableCredit,
  offers,
  onSubmit,
}: BalanceTransferFormProps) {
  const [amount, setAmount] = useState('2000.00');
  const [provider, setProvider] = useState('Example Bank Visa');
  const [last4, setLast4] = useState('5521');
  const [amountError, setAmountError] = useState('');
  const [providerError, setProviderError] = useState('');
  const [last4Error, setLast4Error] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const calculateFee = (val: string): number => {
    const num = parseFloat(val.replace(/[£,]/g, ''));
    return isNaN(num) ? 0 : num * 0.025;
  };

  const validateAmount = (val: string): string => {
    const num = parseFloat(val.replace(/[£,]/g, ''));
    if (isNaN(num)) return 'Enter an amount in pounds and pence, for example 500.00';
    if (num < 1) return 'The amount must be at least £1.00';
    if (num > availableCredit) return `The amount is more than your available credit of £${availableCredit.toFixed(2)}`;
    return '';
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    const amtErr = validateAmount(amount);
    const provErr = provider.trim() ? '' : 'Enter the card provider name';
    const last4Err = /^\d{4}$/.test(last4.trim()) ? '' : 'Enter exactly 4 digits';
    
    setAmountError(amtErr);
    setProviderError(provErr);
    setLast4Error(last4Err);
    
    if (amtErr || provErr || last4Err) {
      return;
    }
    
    const selectedOffer = offers.find(o => o.offer_type === 'BalanceTransfer');
    
    setIsSubmitting(true);
    try {
      await onSubmit({
        amount,
        provider: provider.trim(),
        last4: last4.trim(),
        offerCode: selectedOffer?.offer_code || '',
      });
      setAmount('');
      setProvider('');
      setLast4('');
    } catch {
      // Error handled by parent
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedOffer = offers.find(o => o.offer_type === 'BalanceTransfer');

  return (
    <form onSubmit={handleSubmit}>
      <Stack gap={5}>
        {selectedOffer && (
          <InlineNotification
            kind="info"
            lowContrast
            hideCloseButton
            title="Promotional offer available"
            subtitle={`${selectedOffer.offer_title}: 0% for the promotional period, then your standard rate. A fee of 2.5% of the amount applies.`}
          />
        )}
        
        <TextInput
          id="btAmt"
          labelText="Amount to transfer (£)"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          invalid={!!amountError}
          invalidText={amountError}
          helperText={`Up to your available credit of £${availableCredit.toFixed(2)}. Fee on £${amount}: £${calculateFee(amount).toFixed(2)}`}
        />
        
        <TextInput
          id="btProv"
          labelText="Provider on the card you are moving from"
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          invalid={!!providerError}
          invalidText={providerError}
        />
        
        <TextInput
          id="btLast"
          labelText="Last 4 digits of that card"
          value={last4}
          onChange={(e) => setLast4(e.target.value)}
          maxLength={4}
          invalid={!!last4Error}
          invalidText={last4Error}
          helperText="We only ask for the last 4 digits"
        />
        
        <div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Processing...' : 'Review balance transfer'}
          </Button>
        </div>
      </Stack>
    </form>
  );
}
