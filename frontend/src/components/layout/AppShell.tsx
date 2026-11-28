import { useState } from 'react';
import { Link, Outlet, useLocation, useMatch, useNavigate } from 'react-router-dom';
import {
  Content,
  Header,
  HeaderGlobalBar,
  HeaderMenuButton,
  HeaderName,
  SideNav,
  SideNavDivider,
  SideNavItems,
  SideNavLink,
  SkipToContent,
} from '@carbon/react';
import { UserAvatar } from '@carbon/icons-react';
import { useAuth } from '../../lib/auth-context';
import { useAccounts } from '../../lib/queries';
import { BoundaryBanner } from './BoundaryBanner';

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [expanded, setExpanded] = useState(true);
  const routeMatch = useMatch('/accounts/:accountId/*');
  const accounts = useAccounts({ limit: 1 }, user?.role !== 'administrator');
  const accountId = routeMatch?.params.accountId ?? accounts.data?.items[0]?.id;
  const base = accountId ? `/accounts/${accountId}` : '/accounts';
  const isActive = (path: string) => location.pathname === path;

  const signOut = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <>
      <Header aria-label="Credit card information prototype">
        <SkipToContent href="#main-content">Skip to main content</SkipToContent>
        <HeaderMenuButton
          aria-label={expanded ? 'Close menu' : 'Open menu'}
          aria-controls="side-navigation"
          isActive={expanded}
          isCollapsible
          onClick={() => setExpanded((value) => !value)}
        />
        <HeaderName as={Link} to="/accounts" prefix="Prototype">
          Card information
        </HeaderName>
        <HeaderGlobalBar>
          <span
            className="header-user"
            role="img"
            aria-label={`Signed in as ${user?.username ?? 'unknown user'}`}
            title={user?.username}
          >
            <UserAvatar size={20} />
          </span>
        </HeaderGlobalBar>
        <SideNav
          id="side-navigation"
          aria-label="Side navigation"
          expanded={expanded}
          isFixedNav
          isChildOfHeader
          onOverlayClick={() => setExpanded(false)}
        >
          <SideNavItems>
            <SideNavLink as={Link} to={base} isActive={isActive(base) || location.pathname === '/accounts'} aria-current={isActive(base) || location.pathname === '/accounts' ? 'page' : undefined}>
              Account overview
            </SideNavLink>
            <SideNavLink as={Link} to={accountId ? `${base}/balance` : '/accounts'} isActive={isActive(`${base}/balance`)} aria-current={isActive(`${base}/balance`) ? 'page' : undefined}>
              Balance breakdown
            </SideNavLink>
            <SideNavLink as={Link} to={accountId ? `${base}/transactions` : '/accounts'} isActive={isActive(`${base}/transactions`)} aria-current={isActive(`${base}/transactions`) ? 'page' : undefined}>
              Transactions
            </SideNavLink>
            <SideNavLink as={Link} to={accountId ? `${base}/payments` : '/accounts'} isActive={isActive(`${base}/payments`)} aria-current={isActive(`${base}/payments`) ? 'page' : undefined}>
              Payments
            </SideNavLink>
            <SideNavLink as={Link} to="/data-status" isActive={isActive('/data-status')} aria-current={isActive('/data-status') ? 'page' : undefined}>
              Data status and limitations
            </SideNavLink>
            <SideNavLink as={Link} to="/data-rights" isActive={isActive('/data-rights')} aria-current={isActive('/data-rights') ? 'page' : undefined}>
              Your data rights
            </SideNavLink>
            <SideNavDivider />
            <SideNavLink
              href="#sign-out"
              onClick={(event: React.MouseEvent) => {
                event.preventDefault();
                void signOut();
              }}
            >
              Sign out
            </SideNavLink>
          </SideNavItems>
        </SideNav>
      </Header>
      <Content id="main-content" className={expanded ? 'app-content app-content--nav-open' : 'app-content'}>
        <BoundaryBanner />
        <Outlet />
      </Content>
    </>
  );
}
