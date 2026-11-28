import { InlineNotification } from '@carbon/react';
import { ApiError } from '../../lib/api-client';

interface ErrorNoticeProps {
  error: unknown;
  title?: string;
}

/** Renders `ApiError.detail` in an announced (role=alert) region. */
export function ErrorNotice({ error, title = 'Something went wrong' }: ErrorNoticeProps) {
  const detail = error instanceof ApiError ? error.detail : 'Something went wrong. Try again later.';
  return <InlineNotification role="alert" kind="error" lowContrast hideCloseButton title={title} subtitle={detail} />;
}
