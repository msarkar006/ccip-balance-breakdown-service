import { Navigate, Route, Routes } from 'react-router-dom';
import { Theme } from '@carbon/react';
import { AppShell } from './components/layout/AppShell';
import { RequireAuth } from './components/layout/RequireAuth';
import AccountOverviewPage from './pages/AccountOverviewPage';
import BalanceBreakdownPage from './pages/BalanceBreakdownPage';
import DataRightsPage from './pages/DataRightsPage';
import DataStatusPage from './pages/DataStatusPage';
import LoginPage from './pages/LoginPage';
import PaymentListPage from './pages/PaymentListPage';
import TransactionListPage from './pages/TransactionListPage';

export default function App() {
  return (
    <Theme theme="white">
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route path="/accounts" element={<AccountOverviewPage />} />
            <Route path="/accounts/:accountId" element={<AccountOverviewPage />} />
            <Route path="/accounts/:accountId/balance" element={<BalanceBreakdownPage />} />
            <Route path="/accounts/:accountId/transactions" element={<TransactionListPage />} />
            <Route path="/accounts/:accountId/payments" element={<PaymentListPage />} />
            <Route path="/data-status" element={<DataStatusPage />} />
            <Route path="/data-rights" element={<DataRightsPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/accounts" replace />} />
      </Routes>
    </Theme>
  );
}
