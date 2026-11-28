import type { Page } from './common';

export type DataRightsRequestType = 'export' | 'deletion';

export interface DataRightsRequestCreate {
  requestType: DataRightsRequestType;
  subjectRef?: string;
}

export interface DataRightsRequest {
  id: string;
  subjectRef: string;
  requestType: DataRightsRequestType;
  status: 'received' | 'in_progress' | 'fulfilled' | 'declined';
  requestedAt: string;
  dueAt: string;
  completedAt?: string | null;
  outcomeSummary?: string | null;
}

export type DataRightsRequestPage = Page<DataRightsRequest>;
