import { Link } from 'react-router-dom';
import { SkipToContent } from '@carbon/react';
import { Menu } from '@carbon/icons-react';
import { useAuth } from '../../lib/auth-context';
import styles from './Header.module.scss';

interface HeaderProps {
  onMenuToggle?: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { user, logout } = useAuth();

  return (
    <header className={styles.header}>
      <SkipToContent href="#main-content" />
      {user && onMenuToggle && (
        <button
          onClick={onMenuToggle}
          className={styles.menuButton}
          aria-label="Open menu"
        >
          <Menu size={20} />
        </button>
      )}
      <Link
        to="/account-overview"
        className={`${styles.brandLink} cds--type-body-compact-01`}
      >
        <span className={styles.brandName}>NBS</span> Card servicing
      </Link>
      <div className={styles.headerActions}>
        {user && (
          <>
            <span className={`${styles.userEmail} cds--type-body-compact-01`}>{user.email}</span>
            <button
              onClick={logout}
              className={styles.logoutButton}
            >
              Log out
            </button>
          </>
        )}
        {!user && (
          <span className={`${styles.helpText} cds--type-body-compact-01`}>Help</span>
        )}
      </div>
    </header>
  );
}
