import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

/** The prototype is information-only: no control may be labelled with a financial-action verb. */
const FORBIDDEN = /\b(pay now|make a payment|pay|transfer|schedule|amend|cancel|redeem|enrol|enroll|convert|validate|select|complete|confirm|activate|submit(?! request)|apply|set up)\b/i;

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return name === 'test' ? [] : sourceFiles(path);
    return /\.tsx$/.test(name) ? [path] : [];
  });
}

/** Text inside <Button>, <button>, <SideNavLink>, <Link>, <a> and label-ish props. */
function controlLabels(source: string): string[] {
  const labels: string[] = [];
  const element = /<(Button|button|SideNavLink|Link|a|HeaderMenuItem|IconButton)\b[^>]*>([\s\S]*?)<\/\1>/g;
  for (const match of source.matchAll(element)) labels.push(match[2].replace(/<[^>]+>/g, ' ').replace(/[{}]/g, ' '));
  for (const match of source.matchAll(/\b(aria-label|label|iconDescription|labelText)="([^"]*)"/g)) labels.push(match[2]);
  return labels.map((label) => label.trim()).filter(Boolean);
}

describe('forbidden-verb control-label lint', () => {
  const files = sourceFiles(join(__dirname, '..'));

  it('scans the source tree', () => {
    expect(files.length).toBeGreaterThan(5);
  });

  it.each(files.map((file) => [file.split('/src/')[1], file]))('%s has no action-verb control labels', (_name, file) => {
    const offenders = controlLabels(readFileSync(file, 'utf8')).filter((label) => FORBIDDEN.test(label));
    expect(offenders).toEqual([]);
  });

  it('the pattern itself catches action verbs and spares the allowed nav labels', () => {
    for (const bad of ['Pay now', 'Transfer balance', 'Cancel payment', 'Schedule payment', 'Redeem']) expect(FORBIDDEN.test(bad)).toBe(true);
    for (const ok of ['Payments', 'Sign in', 'Sign out', 'Transactions', 'Your data rights', 'Data status and limitations']) expect(FORBIDDEN.test(ok)).toBe(false);
  });
});
