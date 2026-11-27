import { useState, useEffect } from 'react';
import { Select, SelectItem } from '@carbon/react';
import { Account } from '../../types/account';
import { apiClient } from '../../lib/api-client';

interface AccountSelectorProps {
  selectedAccountId: number | null;
  onAccountChange: (accountId: number) => void;
}

export function AccountSelector({ selectedAccountId, onAccountChange }: AccountSelectorProps) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const response = await apiClient.get<{ accounts: Account[] }>('/v1/accounts');
        setAccounts(response.accounts);
      } catch (error) {
        console.error('Failed to fetch accounts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAccounts();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const accountId = parseInt(e.target.value, 10);
    if (!isNaN(accountId)) {
      onAccountChange(accountId);
    }
  };

  if (loading) {
    return (
      <Select
        id="accountSelect"
        labelText="Account"
        helperText="Loading accounts..."
        disabled
      >
        <SelectItem text="Loading..." value="" />
      </Select>
    );
  }

  return (
    <Select
      id="accountSelect"
      labelText="Account"
      helperText="Changing account updates everything on this page"
      value={selectedAccountId?.toString() || ''}
      onChange={handleChange}
    >
      {accounts.map((account) => (
        <SelectItem
          key={account.id}
          text={`${account.account_number_masked} · ${account.card_number_masked || ''}`}
          value={account.id.toString()}
        />
      ))}
    </Select>
  );
}
