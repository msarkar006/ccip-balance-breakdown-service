import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Loading } from '@carbon/react';
import { useAuth } from '../../lib/auth-context';

/** Route guard: anonymous visitors go to /login; the page they asked for is kept in router state. */
export function RequireAuth() {
  const { status, user } = useAuth();
  const location = useLocation();
  if (status === 'loading') return <Loading withOverlay description="Checking your session" />;
  if (status === 'anonymous') return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (user?.role === 'administrator' && location.pathname !== '/data-rights') return <Navigate to="/data-rights" replace />;
  return <Outlet />;
}
