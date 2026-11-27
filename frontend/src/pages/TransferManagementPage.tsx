import { useState, useEffect } from 'react';
import {
  Grid,
  Column,
  Stack,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Tile,
  InlineNotification,
  Modal,
  TextInput,
} from '@carbon/react';
import { apiClient } from '../lib/api-client';
import { BalanceTransferForm } from '../components/transfer/BalanceTransferForm';
import { MoneyTransferForm } from '../components/transfer/MoneyTransferForm';
import { TransferHistoryTable } from '../components/transfer/TransferHistoryTable';
import type {
  BalanceTransferListResponse,
  MoneyTransferListResponse,
  PayeeListResponse,
  Offer,
  OfferListResponse,
} from '../types/transfer';
import styles from './TransferManagementPage.module.scss';

export function TransferManagementPage() {
  const [selectedAccount] = useState('ACC-1001');
  const [balanceTransfers, setBalanceTransfers] = useState<BalanceTransferListResponse | null>(null);
  const [moneyTransfers, setMoneyTransfers] = useState<MoneyTransferListResponse | null>(null);
  const [payees, setPayees] = useState<PayeeListResponse | null>(null);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [outcome, setOutcome] = useState<{ title: string; message: string } | null>(null);
  const [stepUpModal, setStepUpModal] = useState(false);
  const [stepUpPassword, setStepUpPassword] = useState('');
  const [stepUpPending, setStepUpPending] = useState<((password: string) => Promise<void>) | null>(null);

  const availableCredit = 5137.65;

  useEffect(() => {
    loadData();
  }, [selectedAccount]);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [btRes, mtRes, payeeRes, offerRes] = await Promise.all([
        apiClient.get<BalanceTransferListResponse>(`/v1/balance-transfers?account_id=1&limit=10&offset=0`),
        apiClient.get<MoneyTransferListResponse>(`/v1/money-transfers?account_id=1&limit=10&offset=0`),
        apiClient.get<PayeeListResponse>(`/v1/payees?account_id=1&limit=25&offset=0`),
        apiClient.get<OfferListResponse>(`/v1/offers?account_id=1&context=BalanceTransfer&limit=20&offset=0`),
      ]);
      setBalanceTransfers(btRes);
      setMoneyTransfers(mtRes);
      setPayees(payeeRes);
      setOffers(offerRes.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load transfers');
    } finally {
      setLoading(false);
    }
  };

  const performStepUp = async (password: string): Promise<string> => {
    const response = await apiClient.post<{ success: boolean; valid_until: string }>(
      '/v1/auth/step-up',
      { password }
    );
    return response.valid_until;
  };

  const handleBalanceTransferSubmit = async (data: {
    amount: string;
    provider: string;
    last4: string;
    offerCode: string;
  }) => {
    const executeTransfer = async (password: string) => {
      try {
        const stepUpProof = await performStepUp(password);
        const idempotencyKey = `bt-${Date.now()}-${Math.random()}`;
        
        await apiClient.post(
          '/v1/balance-transfers',
          {
            account_id: 1,
            offer_code: data.offerCode,
            transfer_amount: parseFloat(data.amount.replace(/[£,]/g, '')),
            external_card_last4: data.last4,
            provider_name: data.provider,
            idempotency_key: idempotencyKey,
          },
          {
            'Idempotency-Key': idempotencyKey,
            'X-Step-Up-Proof': stepUpProof,
          }
        );
        
        setOutcome({
          title: 'Balance transfer submitted',
          message: 'We have received your request and it is being checked. It appears at the top of your history below.',
        });
        await loadData();
        setStepUpModal(false);
        setStepUpPassword('');
        setStepUpPending(null);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        }
      }
    };

    setStepUpPending(() => executeTransfer);
    setStepUpModal(true);
  };

  const handleMoneyTransferSubmit = async (data: { payeeId: number; amount: string }) => {
    const executeTransfer = async (password: string) => {
      try {
        const stepUpProof = await performStepUp(password);
        const idempotencyKey = `mt-${Date.now()}-${Math.random()}`;
        
        await apiClient.post(
          '/v1/money-transfers',
          {
            account_id: 1,
            payee_id: data.payeeId,
            amount: parseFloat(data.amount.replace(/[£,]/g, '')),
            currency: 'GBP',
            idempotency_key: idempotencyKey,
          },
          {
            'Idempotency-Key': idempotencyKey,
            'X-Step-Up-Proof': stepUpProof,
          }
        );
        
        setOutcome({
          title: 'Money transfer processing',
          message: 'We have your request and it is processing. The result will appear in the history below.',
        });
        await loadData();
        setStepUpModal(false);
        setStepUpPassword('');
        setStepUpPending(null);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        }
      }
    };

    setStepUpPending(() => executeTransfer);
    setStepUpModal(true);
  };

  if (loading) {
    return (
      <Grid>
        <Column lg={16}>
          <p>Loading transfers...</p>
        </Column>
      </Grid>
    );
  }

  return (
    <Grid>
      <Column lg={16}>
        <Stack gap={7}>
          <div>
            <h1 className="cds--type-heading-04">Transfers</h1>
            <p className="cds--type-helper-text-01">
              Account {selectedAccount} · card **** 4821 · available credit £{availableCredit.toFixed(2)}
            </p>
          </div>

          {error && (
            <InlineNotification
              kind="error"
              lowContrast
              title="Error"
              subtitle={error}
              onCloseButtonClick={() => setError('')}
            />
          )}

          {outcome && (
            <InlineNotification
              kind="info"
              lowContrast
              title={outcome.title}
              subtitle={outcome.message}
              onCloseButtonClick={() => setOutcome(null)}
            />
          )}

          <Tabs>
            <TabList aria-label="Transfer types">
              <Tab>Balance transfer</Tab>
              <Tab>Money transfer</Tab>
            </TabList>
            <TabPanels>
              <TabPanel>
                <Stack gap={7}>
                  <Grid narrow>
                    <Column lg={6}>
                      <Tile className={styles.accentTile}>
                        <Stack gap={5}>
                          <div>
                            <h2 className="cds--type-heading-03">Request a balance transfer</h2>
                            <p className={`cds--type-helper-text-01 ${styles.description}`}>
                              Move a balance from another card to this account. Offer: 0% for the promotional period,
                              then your standard rate. A fee of 2.5% of the amount applies.
                            </p>
                          </div>
                          <BalanceTransferForm
                            availableCredit={availableCredit}
                            offers={offers}
                            onSubmit={handleBalanceTransferSubmit}
                          />
                        </Stack>
                      </Tile>
                    </Column>
                    <Column lg={10}>
                      <Stack gap={5}>
                        <h2 className="cds--type-heading-03">Balance transfer history</h2>
                        {balanceTransfers && balanceTransfers.items.length > 0 ? (
                          <TransferHistoryTable type="balance" transfers={balanceTransfers.items} />
                        ) : (
                          <p className="cds--type-body-01">No balance transfers yet.</p>
                        )}
                      </Stack>
                    </Column>
                  </Grid>
                </Stack>
              </TabPanel>
              <TabPanel>
                <Stack gap={7}>
                  <Grid narrow>
                    <Column lg={6}>
                      <Tile className={styles.accentTile}>
                        <Stack gap={5}>
                          <div>
                            <h2 className="cds--type-heading-03">Transfer money to your bank account</h2>
                            <p className={`cds--type-helper-text-01 ${styles.description}`}>
                              Money transferred from your card is treated as a cash-style transaction. A fee of 3% of
                              the amount applies.
                            </p>
                          </div>
                          {payees && payees.items.length > 0 ? (
                            <MoneyTransferForm
                              availableCredit={availableCredit}
                              payees={payees.items}
                              onSubmit={handleMoneyTransferSubmit}
                            />
                          ) : (
                            <p className="cds--type-body-01">No payees available. Add a payee to transfer money.</p>
                          )}
                        </Stack>
                      </Tile>
                    </Column>
                    <Column lg={10}>
                      <Stack gap={5}>
                        <h2 className="cds--type-heading-03">Money transfer history</h2>
                        {moneyTransfers && moneyTransfers.items.length > 0 ? (
                          <TransferHistoryTable type="money" transfers={moneyTransfers.items} />
                        ) : (
                          <p className="cds--type-body-01">No money transfers yet.</p>
                        )}
                      </Stack>
                    </Column>
                  </Grid>
                </Stack>
              </TabPanel>
            </TabPanels>
          </Tabs>

          <Modal
            open={stepUpModal}
            onRequestClose={() => {
              setStepUpModal(false);
              setStepUpPassword('');
              setStepUpPending(null);
            }}
            onRequestSubmit={async () => {
              if (stepUpPending) {
                await stepUpPending(stepUpPassword);
              }
            }}
            modalHeading="Confirm your identity"
            primaryButtonText="Confirm and submit"
            secondaryButtonText="Cancel"
          >
            <Stack gap={5}>
              <p>For your security, please confirm your password before we submit this request.</p>
              <TextInput
                id="stepUpPassword"
                type="password"
                labelText="Password"
                value={stepUpPassword}
                onChange={(e) => setStepUpPassword(e.target.value)}
              />
            </Stack>
          </Modal>
        </Stack>
      </Column>
    </Grid>
  );
}
