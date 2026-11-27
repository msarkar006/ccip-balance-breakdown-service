import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.scss';

interface SidebarProps {
  isOpen: boolean;
}

export function Sidebar({ isOpen }: SidebarProps) {
  const navItems = [
    { path: '/account-overview', label: 'Account overview' },
    { path: '/balance-breakdown', label: 'Balance breakdown' },
    { path: '/payments', label: 'Payments and direct debit' },
    { path: '/transfers', label: 'Transfers' },
    { path: '/rewards', label: 'Rewards and offers' },
    { path: '/activity', label: 'Activity tracker' },
    { path: '/tracker', label: 'Unified tracker' },
  ];

  return (
    <nav
      className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}
      aria-label="Side navigation"
    >
      <ul className={styles.navList}>
        {navItems.map((item) => (
          <li key={item.path} className={styles.navItem}>
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                `${styles.navLink} ${isActive ? styles.active : ''}`
              }
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
