import { useState, useEffect, useCallback } from 'react';
import { Grid, Column, Stack, Select, SelectItem, DataTable, Table, TableHead, TableRow, TableHeader, TableBody, TableCell, InlineNotification, Tile, Button } from '@carbon/react';
import { View } from '@carbon/icons-react';
import { Link, useNavigate } from 'react-router-dom';
import { apiClient } from '../lib/api-client';

interface InstalmentPlan {
  id: number;
  plan_reference: string;
  plan_name: string;
  original_amount: string;
  remaining_balance: string;
  instalment_count: number;
  monthly_payment: string;
  apr: string;
  status: string;
  created_at: string;
}

interface InstalmentPlanListResponse {
  items: InstalmentPlan[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  empty_state_message: string | null;
}

export function InstalmentReviewPage() {
  const navigate = useNavigate();
  const [selectedAccount, setSelectedAccount] = useState('ACC-1001');
  const [accountId, setAccountId] = useState(1);
  const [data, setData] = useState<InstalmentPlanListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get<InstalmentPlanListResponse>(`/v1/instalments?account_id=${accountId}&instalment_status=Active`);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load instalment plans');
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

  const handleViewDetails = (planId: number) => {
    // Navigate to detail page (would be implemented)
    console.log('View instalment plan', planId);
  };

  if (loading) {
    return (
      <Grid>
        <Column lg={16}>
          <p>Loading instalment plans...</p>
        </Column>
      </Grid>
    );
  }

  const isEmpty = !data?.items || data.items.length === 0;

  const headers = [
    { key: 'plan_name', header: 'Plan name' },
    { key: 'remaining_balance', header: 'Remaining balance' },
    { key: 'monthly_payment', header: 'Monthly payment' },
    { key: 'apr', header: 'APR' },
    { key: 'status', header: 'Status' },
    { key: 'actions', header: '' },
  ];

  const rows = data?.items.map((plan) => ({
    id: plan.id.toString(),
    plan_name: plan.plan_name,
    remaining_balance: `£${plan.remaining_balance}`,
    monthly_payment: `£${plan.monthly_payment}`,
    apr: `${plan.apr}%`,
    status: plan.status,
    actions: plan.id,
  })) || [];

  return (
    <Grid>
      <Column lg={16}>
        <Stack gap={7}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h1 className="cds--type-heading-04">Instalment plans</h1>
              <p className="cds--type-helper-text-01">
                Account {selectedAccount} · card **** {selectedAccount === 'ACC-1001' ? '4821' : '2231'}
              </p>
            </div>
            <div style={{ minWidth: '240px' }}>
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
                <h2 className="cds--type-heading-03">No instalment plans found</h2>
                <p className="cds--type-body-01">
                  {data?.empty_state_message || 'This account has no active instalment plans.'}
                </p>
                <div>
                  <Link to="/account-overview" className="cds--btn cds--btn--tertiary">
                    Back to account overview
                  </Link>
                </div>
              </Stack>
            </Tile>
          ) : (
            <section>
              <Stack gap={5}>
                <div>
                  <h2 className="cds--type-heading-03">Active plans</h2>
                  <p className="cds--type-helper-text-01">
                    Your active instalment plans for this account. Showing {data?.items.length} of {data?.total} plan{data?.total !== 1 ? 's' : ''}.
                  </p>
                </div>
                <DataTable rows={rows} headers={headers}>
                  {({ rows, headers, getTableProps, getHeaderProps, getRowProps }: any) => (
                    <Table {...getTableProps()}>
                      <TableHead>
                        <TableRow>
                          {headers.map((header: any) => (
                            <TableHeader {...getHeaderProps({ header })} key={header.key}>
                              {header.header}
                            </TableHeader>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {rows.map((row: any) => (
                          <TableRow {...getRowProps({ row })} key={row.id}>
                            {row.cells.map((cell: any) => (
                              <TableCell key={cell.id}>
                                {cell.info.header === 'actions' ? (
                                  <Button
                                    kind="ghost"
                                    size="sm"
                                    renderIcon={View}
                                    iconDescription="View details"
                                    hasIconOnly
                                    onClick={() => handleViewDetails(parseInt(cell.value))}
                                  />
                                ) : (
                                  cell.value
                                )}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </DataTable>
              </Stack>
            </section>
          )}
        </Stack>
      </Column>
    </Grid>
  );
}
