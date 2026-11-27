import { useState, useEffect, useCallback } from 'react';
import { Grid, Column, Stack, Select, SelectItem, Tile, InlineNotification } from '@carbon/react';
import { Link } from 'react-router-dom';
import { apiClient } from '../lib/api-client';
import { RewardsSummary } from '../components/rewards/RewardsSummary';
import { OfferList } from '../components/rewards/OfferList';
import type { RewardsSummaryResponse } from '../types/rewards';
import styles from './RewardsOffersPage.module.scss';

export function RewardsOffersPage() {
  const [selectedAccount, setSelectedAccount] = useState('ACC-1001');
  const [accountId, setAccountId] = useState(1);
  const [data, setData] = useState<RewardsSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get<RewardsSummaryResponse>(`/v1/rewards?account_id=${accountId}`);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load rewards data');
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAccountChange = (value: string) => {
    setSelectedAccount(value);
    setAccountId(value === 'ACC-1001' ? 1 : 2);
  };

  if (loading) {
    return (
      <Grid>
        <Column lg={16}>
          <p>Loading rewards and offers...</p>
        </Column>
      </Grid>
    );
  }

  const isEmpty = !data?.programme && (!data?.relevant_offers || data.relevant_offers.length === 0);

  return (
    <Grid>
      <Column lg={16}>
        <Stack gap={7}>
          <div className={styles.pageHeader}>
            <div>
              <h1 className="cds--type-heading-04">Rewards and offers</h1>
              <p className="cds--type-helper-text-01">
                Account {selectedAccount} · card **** {selectedAccount === 'ACC-1001' ? '4821' : '2231'}
              </p>
            </div>
            <div className={styles.accountSelector}>
              <Select
                id="accountSelect"
                labelText="Account"
                value={selectedAccount}
                onChange={(e) => handleAccountChange(e.target.value)}
              >
                <SelectItem value="ACC-1001" text="ACC-1001 · **** 4821" />
                <SelectItem value="ACC-1002" text="ACC-1002 · **** 2231" />
              </Select>
            </div>
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

          {isEmpty ? (
            <Tile>
              <Stack gap={5}>
                <h2 className="cds--type-heading-03">Nothing to show for this account right now</h2>
                <p className="cds--type-body-01">
                  This account has no rewards programme and no offers available at the moment. You can still view your
                  balance, make payments and track requests.
                </p>
                <div>
                  <Link to="/account-overview" className="cds--btn cds--btn--tertiary">
                    Back to account overview
                  </Link>
                </div>
              </Stack>
            </Tile>
          ) : (
            <>
              {data?.programme && (
                <section>
                  <Grid narrow>
                    <Column lg={6}>
                      <Stack gap={5}>
                        <h2 className="cds--type-heading-03">Your rewards</h2>
                        <RewardsSummary programme={data.programme} />
                      </Stack>
                    </Column>
                    <Column lg={10}>
                      <Tile>
                        <Stack gap={5}>
                          <h3 className="cds--type-heading-02">About your points</h3>
                          <p className="cds--type-body-01">
                            Points shown here are a summary. The rewards programme provider holds your full rewards
                            history, so the balance can be slightly behind recent purchases.
                          </p>
                          <p className="cds--type-helper-text-01">
                            Redeeming points and rewards history are not available in this service.
                          </p>
                        </Stack>
                      </Tile>
                    </Column>
                  </Grid>
                </section>
              )}

              {data?.relevant_offers && data.relevant_offers.length > 0 && (
                <section>
                  <Stack gap={5}>
                    <div>
                      <h2 className="cds--type-heading-03">Offers for this account</h2>
                      <p className="cds--type-helper-text-01">
                        Only offers you can use on this account are shown. Offers that do not apply to you are not listed.
                      </p>
                    </div>
                    <OfferList offers={data.relevant_offers} />
                  </Stack>
                </section>
              )}
            </>
          )}
        </Stack>
      </Column>
    </Grid>
  );
}
