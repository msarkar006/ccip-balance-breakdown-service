import { Routes, Route, Navigate } from 'react-router-dom';
import { Theme } from '@carbon/react';
import { RequireAuth } from './components/auth/RequireAuth';
import { Layout } from './components/layout/Layout';
import { LoginPage } from './pages/LoginPage';
import { AccountOverviewPage } from './pages/AccountOverviewPage';
import { BalanceBreakdownPage } from './pages/BalanceBreakdownPage';
import { TransactionHistoryPage } from './pages/TransactionHistoryPage';
import { PaymentManagementPage } from './pages/PaymentManagementPage';
import { TrackingActivityPage } from './pages/TrackingActivityPage';
import { TransferManagementPage } from './pages/TransferManagementPage';
import { RewardsOffersPage } from './pages/RewardsOffersPage';
import { InstalmentReviewPage } from './pages/InstalmentReviewPage';

function App() {
  return (
    <Theme theme="white">
      <Routes>
        <Route
          path="/login"
          element={
            <Layout>
              <LoginPage />
            </Layout>
          }
        />
        <Route
          path="/account-overview"
          element={
            <RequireAuth>
              <Layout>
                <AccountOverviewPage />
              </Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/balance-breakdown"
          element={
            <RequireAuth>
              <Layout>
                <BalanceBreakdownPage />
              </Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/activity"
          element={
            <RequireAuth>
              <Layout>
                <TransactionHistoryPage />
              </Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/payments"
          element={
            <RequireAuth>
              <Layout>
                <PaymentManagementPage />
              </Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/tracker"
          element={
            <RequireAuth>
              <Layout>
                <TrackingActivityPage />
              </Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/transfers"
          element={
            <RequireAuth>
              <Layout>
                <TransferManagementPage />
              </Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/rewards"
          element={
            <RequireAuth>
              <Layout>
                <RewardsOffersPage />
              </Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/instalments"
          element={
            <RequireAuth>
              <Layout>
                <InstalmentReviewPage />
              </Layout>
            </RequireAuth>
          }
        />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Theme>
  );
}

export default App;
