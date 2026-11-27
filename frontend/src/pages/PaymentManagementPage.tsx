import { useState, useEffect } from 'react';
import { Stack, Grid, Column, Heading, InlineNotification, Tile } from '@carbon/react';
import { apiClient } from '../lib/api-client';
import { PaymentGuidance, PaymentListResponse, PaymentInitiationResponse } from '../types/payment';
import { PaymentForm } from '../components/payment/PaymentForm';
import { PaymentHistoryTable } from '../components/payment/PaymentHistoryTable';
import { formatCurrency, formatDate } from '../lib/utils';
import styles from './PaymentManagementPage.module.scss';

export function PaymentManagementPage() {
  const [guidance, setGuidance] = useState<PaymentGuidance | null>(null);
  const [payments, setPayments] = useState<PaymentListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const accountId = 1; // TODO: Get from selected account context

  const fetchData = async () => {
    setIsLoading(true);
    setError('');

    try {
      const [guidanceData, paymentsData] = await Promise.all([
        apiClient.get<PaymentGuidance>(`/v1/payments/guidance?account_id=${accountId}`),
        apiClient.get<PaymentListResponse>(`/v1/payments?account_id=${accountId}&limit=20&offset=0`),
      ]);

      setGuidance(guidanceData);
      setPayments(paymentsData);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load payment information');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handlePaymentSuccess = (payment: PaymentInitiationResponse) => {
    setSuccessMessage(
      payment.scheduled_date
        ? `Payment of ${formatCurrency(parseFloat(payment.amount))} scheduled for ${formatDate(payment.scheduled_date)}`
        : `Payment of ${formatCurrency(parseFloat(payment.amount))} submitted successfully`
    );
    fetchData();
  };

  const renderDirectDebitCoverage = () => {
    if (!guidance) return null;

    const { coverage_status, manual_payment_may_be_required, reason } = guidance.direct_debit_coverage;

    let kind: 'success' | 'warning' | 'info' = 'info';
    let title = '';
    let subtitle = reason;

    if (coverage_status === 'expected_to_cover') {
      kind = 'success';
      title = 'Direct debit will cover minimum payment';
    } else if (coverage_status === 'not_expected_to_cover') {
      kind = 'warning';
      title = 'Direct debit may not cover full minimum payment';
    } else {
      kind = 'info';
      title = 'Direct debit coverage cannot be confirmed';
    }

    if (manual_payment_may_be_required) {
      subtitle += ' You may need to make a manual payment.';
    }

    return (
      <InlineNotification
        kind={kind}
        title={title}
        subtitle={subtitle}
        lowContrast
        hideCloseButton
        className={styles.notification}
      />
    );
  };

  if (isLoading) {
    return (
      <div>
        <Heading>Payment Management</Heading>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Stack gap={7}>
      <div>
        <Heading>Payment Management</Heading>
        <p className={`cds--label-01 ${styles.pageSubtitle}`}>
          Account ACC-1001 · Manage payments and direct debit
        </p>
      </div>

      {error && (
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={error}
          lowContrast
          onCloseButtonClick={() => setError('')}
        />
      )}

      {successMessage && (
        <InlineNotification
          kind="success"
          title="Payment submitted"
          subtitle={successMessage}
          lowContrast
          onCloseButtonClick={() => setSuccessMessage('')}
        />
      )}

      <Grid>
        <Column lg={6} md={8} sm={4}>
          <Tile className={styles.accentTile}>
            <Stack gap={5}>
              <h2 className="cds--productive-heading-03">
                Make a payment
              </h2>

              {guidance && (
                <div className={styles.guidanceGrid}>
                  <div className={styles.guidanceItem}>
                    <div className={`cds--label-01 ${styles.guidanceLabel}`}>
                      Minimum payment
                    </div>
                    <div className={`cds--productive-heading-03 ${styles.guidanceFigure}`}>
                      {formatCurrency(parseFloat(guidance.minimum_payment))}
                    </div>
                  </div>
                  <div className={styles.guidanceItem}>
                    <div className={`cds--label-01 ${styles.guidanceLabel}`}>
                      Due by
                    </div>
                    <div className={`cds--productive-heading-03 ${styles.guidanceFigure}`}>
                      {formatDate(guidance.due_date)}
                    </div>
                  </div>
                  <div className={styles.guidanceItem}>
                    <div className={`cds--label-01 ${styles.guidanceLabel}`}>
                      Current balance
                    </div>
                    <div className="cds--body-01">{formatCurrency(parseFloat(guidance.current_balance))}</div>
                  </div>
                </div>
              )}

              {renderDirectDebitCoverage()}

              {guidance && (
                <PaymentForm
                  accountId={accountId}
                  minimumPayment={guidance.minimum_payment}
                  currentBalance={guidance.current_balance}
                  onSuccess={handlePaymentSuccess}
                />
              )}
            </Stack>
          </Tile>
        </Column>
      </Grid>

      <section>
        <h2 className={`cds--productive-heading-03 ${styles.sectionHeading}`}>
          Payment history
        </h2>
        {payments && payments.items.length > 0 ? (
          <PaymentHistoryTable payments={payments.items} onRefresh={fetchData} />
        ) : (
          <InlineNotification
            kind="info"
            title="No payments found"
            subtitle="You have no payment history for this account"
            lowContrast
            hideCloseButton
          />
        )}
      </section>
    </Stack>
  );
}
