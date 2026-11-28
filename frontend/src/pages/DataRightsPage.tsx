import { useState } from 'react';
import { InlineLoading, InlineNotification } from '@carbon/react';
import { ApiError, newCorrelationId, post } from '../lib/api-client';
import { useAuth } from '../lib/auth-context';
import { useApiQuery } from '../lib/queries';
import { ErrorNotice } from '../components/common/ErrorNotice';
import { DataRightsForm, type DataRightsFormValues } from '../components/datarights/DataRightsForm';
import { DataRightsRequestList } from '../components/datarights/DataRightsRequestList';
import type { DataRightsRequest, DataRightsRequestPage } from '../types/dataRights';
import '../components/datarights/datarights.css';

type Outcome = { kind: 'submitted' } | { kind: 'failed'; error: unknown } | null;

/** Privacy workflow: creates a data-rights record only, never a servicing action. */
export default function DataRightsPage() {
  const { user } = useAuth();
  const list = useApiQuery<DataRightsRequestPage>('/data-rights-requests');
  const [submitting, setSubmitting] = useState(false);
  const [outcome, setOutcome] = useState<Outcome>(null);

  const submit = async (values: DataRightsFormValues) => {
    setSubmitting(true);
    setOutcome(null);
    try {
      // A fresh key per submit: a retry of the same click is never a duplicate, a new click is a new request.
      await post<DataRightsRequest>('/data-rights-requests', values, { 'Idempotency-Key': newCorrelationId() });
      setOutcome({ kind: 'submitted' });
      list.reload();
    } catch (error: unknown) {
      setOutcome({ kind: 'failed', error: error instanceof ApiError ? error : null });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section aria-labelledby="page-heading">
      <h1 id="page-heading" className="page-title">
        Your data rights
      </h1>
      <p className="page-lead">
        Ask for an export or deletion of the synthetic data held about you. A request is recorded and audited. It is a
        privacy workflow, not a servicing action.
      </p>
      <div role="note">
        <InlineNotification
          kind="info"
          lowContrast
          hideCloseButton
          title="What this does and does not do"
          subtitle="A request creates a record that is tracked to completion within 30 calendar days. It does not change any account, card, payment or other record, and it does not make a financial request."
        />
      </div>
      <DataRightsForm onSubmit={submit} submitting={submitting} requireSubject={user?.role === 'administrator'} />
      <div className="dr-result" aria-live="polite">
        {outcome?.kind === 'submitted' ? (
          <InlineNotification
            role="status"
            kind="info"
            lowContrast
            hideCloseButton
            title="Request received"
            subtitle="Your request has been recorded and is due within 30 calendar days. It appears in the list below."
          />
        ) : null}
        {outcome?.kind === 'failed' ? (
          <ErrorNotice error={outcome.error} title="Request not recorded" />
        ) : null}
      </div>
      <h2 className="cds--productive-heading-03">Your requests</h2>
      {list.loading && !list.data ? <InlineLoading status="active" description="Loading your requests" role="status" /> : null}
      {list.error ? <ErrorNotice error={list.error} title="Your requests could not be loaded" /> : null}
      {list.data ? <DataRightsRequestList requests={list.data.items} /> : null}
    </section>
  );
}
