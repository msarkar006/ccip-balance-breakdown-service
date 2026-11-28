import { InlineNotification } from '@carbon/react';

/** Persistent boundary banner shown on every screen (wireframes 1-7). */
export function BoundaryBanner() {
  return (
    <div role="note" className="boundary-banner">
      <InlineNotification
        kind="info"
        lowContrast
        hideCloseButton
        title="Read-only prototype using synthetic data"
        subtitle="Every value is a separate source field. A status or date shown here does not confirm that any action is available."
      />
    </div>
  );
}
