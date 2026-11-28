import { Tag } from '@carbon/react';

/** Shows a source status verbatim. Neutral colour: a status never implies finality or an available action. */
export function StatusTag({ status }: { status: string }) {
  return (
    <Tag type="gray" size="md">
      {status}
    </Tag>
  );
}
