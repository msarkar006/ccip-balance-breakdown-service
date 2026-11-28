import { Accordion, AccordionItem, InlineNotification, Tag } from '@carbon/react';
import { Time } from '@carbon/icons-react';

const LABELS = [
  {
    label: 'freshness unavailable',
    when: 'The source gave no timestamp for the values.',
    not: 'It does not mean the values are old or new. Currency is unknown.',
  },
  {
    label: 'unconfirmed freshness',
    when: 'A source timestamp exists, but no maximum age has been approved.',
    not: 'It does not mean fresh, stale, real-time or near-real-time.',
  },
  {
    label: 'stale',
    when: 'An approved maximum age has been reached or passed.',
    not: 'It does not mean the values are wrong, only that they are older than the approved limit.',
  },
];

const KEEP_IN_MIND = [
  'Current balance, statement balance, available credit, total outstanding, pending total and minimum payment are different values. They are never combined or swapped.',
  'Pending is not posted. A zero balance does not remove a pending amount.',
  'Transaction date, posted date, payment date, statement date and due date are different dates and carry separate labels.',
  'A status such as Processing, Submitted or Completed is shown as the source supplied it. It is not a promise of timing, outcome or finality.',
  'Rates, dates and fees shown with a balance category are source information for that category. They are not a pricing promise.',
  'If a refresh fails, the last approved time and status stay on screen with their freshness label. They are not described as current.',
  'No real-time, notification or availability promise is made anywhere in this prototype.',
];

/** Static explanatory page: makes no network call. */
export default function DataStatusPage() {
  return (
    <section aria-labelledby="page-heading">
      <h1 id="page-heading" className="page-title">
        Data status and limitations
      </h1>
      <p className="page-lead">
        How to read the dates, freshness labels and statuses shown in this prototype. Nothing here is a service-level commitment.
      </p>
      <InlineNotification
        role="status"
        kind="info"
        lowContrast
        hideCloseButton
        title="Synthetic data, read-only"
        subtitle="This prototype uses approved synthetic data only. It has no live connection to any bank system, and it offers no payment or other financial action."
      />

      <h2 className="section-title">Freshness labels</h2>
      <p className="helper-text">
        Each source time is shown with one of three labels. The label is decided by fixed rules, not by how the page looks.
      </p>
      <table className="data-status-table">
        <caption>Freshness labels and what they mean</caption>
        <thead>
          <tr>
            <th scope="col">Label</th>
            <th scope="col">When it is shown</th>
            <th scope="col">What it does not mean</th>
          </tr>
        </thead>
        <tbody>
          {LABELS.map((row) => (
            <tr key={row.label}>
              <td data-label="Label">
                <Tag type="gray" size="md">
                  {row.label}
                </Tag>
              </td>
              <td data-label="When it is shown">{row.when}</td>
              <td data-label="What it does not mean">{row.not}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="helper-text">At present no maximum age is approved, so a source timestamp is shown as unconfirmed freshness.</p>

      <h2 className="section-title">Example from this prototype</h2>
      <section className="data-status-tile" aria-labelledby="example-heading">
        <h3 id="example-heading" className="group-title">
          Balance breakdown BBD-1
        </h3>
        <div className="data-status-timeline">
          <Time size={20} aria-hidden="true" />
          <span>
            As of <time dateTime="2026-11-24T08:15:00Z">24 Nov 2026, 08:15 UTC</time>
          </span>
          <Tag type="gray" size="md">
            unconfirmed freshness
          </Tag>
        </div>
        <p className="helper-text">The source as-of time is shown exactly as supplied. It is never replaced by the time the page was loaded.</p>
      </section>

      <h2 className="section-title">What to keep in mind</h2>
      <ul className="data-status-list">
        {KEEP_IN_MIND.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2 className="section-title">Other states of this screen</h2>
      <InlineNotification
        role="status"
        kind="warning"
        lowContrast
        hideCloseButton
        title="Source information could not be refreshed"
        subtitle="The last approved values are shown with their original source time. Their freshness label is unchanged. Open the page that shows the value to see it."
      />

      <Accordion className="design-notes">
        <AccordionItem title="Design notes for this wireframe">
          <ul>
            <li><strong>Content:</strong> the three freshness labels use fixed wording. No age threshold is shown because none is approved.</li>
            <li><strong>Source:</strong> the freshness label and basis are returned by the read endpoints; this page is static explanatory content.</li>
          </ul>
        </AccordionItem>
      </Accordion>
    </section>
  );
}
