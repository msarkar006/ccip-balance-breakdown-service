import { Tag } from '@carbon/react';
import { formatUtcDateTime } from '../../lib/format';
import type { Freshness } from '../../types/common';

/** Prints `freshness.state` verbatim, with the source time when the source supplied one. */
export function FreshnessBadge({ freshness }: { freshness: Freshness }) {
  return (
    <span className="inline-flex flex-wrap items-center gap-2">
      <Tag type="gray" size="md">
        {freshness.state}
      </Tag>
      {freshness.sourceTime ? (
        <span>
          Source time: <time dateTime={freshness.sourceTime}>{formatUtcDateTime(freshness.sourceTime)}</time>
        </span>
      ) : null}
    </span>
  );
}
