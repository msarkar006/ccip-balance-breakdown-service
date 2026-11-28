import type { ReactNode } from 'react';

export const NOT_SUPPLIED = 'Not supplied';

interface LabelledValueProps {
  label: string;
  /** null, undefined or an empty string render as "Not supplied"; 0 and "0.00" are real values. */
  value: ReactNode | null | undefined;
}

export function LabelledValue({ label, value }: LabelledValueProps) {
  const absent = value === null || value === undefined || value === '';
  return (
    <div className="labelled-value">
      <dt className="labelled-value__label">{label}</dt>
      <dd className="labelled-value__value">{absent ? NOT_SUPPLIED : value}</dd>
    </div>
  );
}
