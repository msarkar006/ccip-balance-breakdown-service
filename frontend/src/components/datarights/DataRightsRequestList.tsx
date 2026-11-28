import type { DataRightsRequest } from '../../types/dataRights';
import { LabelledValue } from '../common/LabelledValue';
import { StatusTag } from '../common/StatusTag';
import { formatDate, formatUtcDateTime } from '../../lib/format';
import './datarights.css';

const STATUS_LABEL: Record<DataRightsRequest['status'], string> = {
  received: 'Received',
  in_progress: 'In progress',
  fulfilled: 'Fulfilled',
  declined: 'Declined',
};

const TYPE_LABEL: Record<DataRightsRequest['requestType'], string> = {
  export: 'Export',
  deletion: 'Deletion',
};

export function DataRightsRequestList({ requests }: { requests: DataRightsRequest[] }) {
  if (requests.length === 0) {
    return <p className="dr-empty">You have not made any data rights requests.</p>;
  }
  return (
    <>
      {requests.map((request) => (
        <section className="dr-tile" key={request.id} aria-labelledby={`dr-${request.id}`}>
          <h3 className="dr-tile__title" id={`dr-${request.id}`}>
            Request <span className="dr-mono">{request.subjectRef}</span>{' '}
            <StatusTag status={`Status: ${STATUS_LABEL[request.status]}`} />
          </h3>
          <dl className="dr-tile__dl">
            <LabelledValue label="Request type" value={TYPE_LABEL[request.requestType]} />
            <LabelledValue
              label="Requested at"
              value={<time dateTime={request.requestedAt}>{formatUtcDateTime(request.requestedAt)}</time>}
            />
            <LabelledValue
              label="Due by"
              value={<time dateTime={request.dueAt}>{formatDate(request.dueAt.slice(0, 10))}</time>}
            />
            <LabelledValue
              label="Completed at"
              value={
                request.completedAt ? (
                  <time dateTime={request.completedAt}>{formatUtcDateTime(request.completedAt)}</time>
                ) : (
                  'Not yet'
                )
              }
            />
          </dl>
          {request.outcomeSummary ? <p className="dr-helper">{request.outcomeSummary}</p> : null}
          <p className="dr-helper">Status is the recorded workflow status. No completion time is promised.</p>
        </section>
      ))}
    </>
  );
}
