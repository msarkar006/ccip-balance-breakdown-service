import type { Freshness, Money, Page } from './common';

export interface Transaction {
  id: string;
  accountId: string;
  cardId?: string | null;
  sourceRef?: string | null;
  maskedPan?: string | null;
  transactionStatus: 'Pending' | 'Posted';
  transactionTime: string;
  postedDate?: string | null;
  transactionAmount: Money;
  merchantName?: string | null;
  merchantCategoryCode?: string | null;
  eligibleForInstalment?: boolean | null;
  freshness: Freshness;
}

export type TransactionPage = Page<Transaction>;

export interface Payment {
  id: string;
  accountId: string;
  sourceRef?: string | null;
  viaMandateRef?: string | null;
  paymentType: 'OneOff' | 'Scheduled' | 'DirectDebitCollection';
  paymentMethod: 'FasterPayments' | 'DebitCard' | 'DirectDebit';
  paymentStatus: 'Completed' | 'Processing' | 'Failed' | 'Submitted' | 'Cancelled';
  paymentAmount: Money;
  paymentDate: string;
  sourceBankName?: string | null;
  sourceMaskedAccount?: string | null;
  freshness: Freshness;
  informationalNotice: string;
}

export type PaymentPage = Page<Payment>;

export interface TrackingEvent {
  id: string;
  accountId: string;
  transactionId?: string | null;
  paymentId?: string | null;
  trackedEntityType: 'account' | 'transaction' | 'payment';
  trackedEntityId: string;
  lifecycleStatus: string;
  sourceTime?: string | null;
  provenance: string;
  occurredAt: string;
  freshness: Freshness;
}

export type TrackingEventPage = Page<TrackingEvent>;
