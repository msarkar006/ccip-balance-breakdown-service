import type { Freshness, Money, Page, Percent } from './common';

export interface Account {
  id: string;
  sourceRef?: string | null;
  productName: string;
  accountStatus: string;
  openedOn?: string | null;
  currency: string;
  creditLimit?: Money | null;
  availableCredit?: Money | null;
  currentBalance?: Money | null;
  standardPurchaseApr?: Percent | null;
  lastStatementBalance?: Money | null;
  nextStatementDate?: string | null;
  paymentDueDate?: string | null;
  minimumPayment?: Money | null;
  freshness: Freshness;
  informationalNotice: string;
}

export type AccountPage = Page<Account>;

export interface Card {
  id: string;
  accountId: string;
  sourceRef?: string | null;
  maskedPan: string;
  cardStatus: 'Active' | 'PendingActivation';
  expiryMonthYear?: string | null;
  isDigital?: boolean | null;
}

export type CardPage = Page<Card>;

export interface BalanceBreakdownSummary {
  id: string;
  accountId: string;
  sourceRef?: string | null;
  asOf?: string | null;
  totalOutstanding?: Money | null;
  pendingTotal?: Money | null;
  isZeroBalance?: boolean | null;
  freshness: Freshness;
}

export type BalanceBreakdownSummaryPage = Page<BalanceBreakdownSummary>;

export type BalanceCategoryType = 'StandardPurchase' | 'PromotionalPurchase' | 'BalanceTransfer' | 'Instalment';

export interface BalanceCategory {
  id: string;
  sourceRef?: string | null;
  categoryType: BalanceCategoryType;
  categoryLabel: string;
  displayRank: number;
  categoryBalance?: Money | null;
  categoryAprPercent?: Percent | null;
  promoEndDate?: string | null;
  revertRatePercent?: Percent | null;
  daysToExpiry?: number | null;
  sourceBalanceTransferRef?: string | null;
  sourceInstalmentPlanRef?: string | null;
  qualifierNotice?: string | null;
}

export interface BalanceBreakdown {
  id: string;
  accountId: string;
  sourceRef?: string | null;
  asOf?: string | null;
  totalOutstanding?: Money | null;
  pendingTotal?: Money | null;
  isZeroBalance?: boolean | null;
  purchasesSubtotal?: Money | null;
  balanceTransfersSubtotal?: Money | null;
  categories: BalanceCategory[];
  freshness: Freshness;
  notice: string;
}
