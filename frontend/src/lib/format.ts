const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** "22 Nov 2026, 14:05 UTC" from an ISO date-time; returns the input unchanged if it cannot be parsed. */
export function formatUtcDateTime(iso: string): string {
  // The API may send UTC times without a zone designator; treat those as UTC, never as local time.
  const zoned = /(Z|[+-]\d{2}:?\d{2})$/i.test(iso) ? iso : `${iso}Z`;
  const date = new Date(zoned);
  if (Number.isNaN(date.getTime())) return iso;
  const hh = String(date.getUTCHours()).padStart(2, '0');
  const mm = String(date.getUTCMinutes()).padStart(2, '0');
  return `${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}, ${hh}:${mm} UTC`;
}

/** "5 Dec 2026" from a YYYY-MM-DD calendar date. */
export function formatDate(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(isoDate);
  if (!match) return isoDate;
  return `${Number(match[3])} ${MONTHS[Number(match[2]) - 1]} ${match[1]}`;
}

const CURRENCY_SYMBOLS: Record<string, string> = { GBP: '£', USD: '$', EUR: '€' };

/** "£4,862.35" from a decimal string such as "4862.35". Works on the string, never on floats. Absent stays null. */
export function formatMoney(value: string | null | undefined, currency = 'GBP'): string | null {
  if (value === null || value === undefined || value === '') return null;
  const match = /^(-?)(\d+)(\.\d+)?$/.exec(value);
  if (!match) return value;
  const grouped = match[2].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  const symbol = CURRENCY_SYMBOLS[currency] ?? `${currency} `;
  return `${match[1]}${symbol}${grouped}${match[3] ?? ''}`;
}

/** "22.9%" from "22.9". Absent stays null. */
export function formatPercent(value: string | null | undefined): string | null {
  if (value === null || value === undefined || value === '') return null;
  return `${value}%`;
}

/** "09/2028" from "2028-09". */
export function formatExpiry(value: string | null | undefined): string | null {
  if (value === null || value === undefined || value === '') return null;
  const match = /^(\d{4})-(\d{2})$/.exec(value);
  return match ? `${match[2]}/${match[1]}` : value;
}

/** Yes / No for a source boolean; null stays null. */
export function formatYesNo(value: boolean | null | undefined): string | null {
  if (value === null || value === undefined) return null;
  return value ? 'Yes' : 'No';
}
