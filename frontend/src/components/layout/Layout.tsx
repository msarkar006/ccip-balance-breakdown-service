import { useState } from 'react';
import { Content } from '@carbon/react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { useAuth } from '../../lib/auth-context';
import styles from './Layout.module.scss';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className={styles.layoutContainer}>
      <Header onMenuToggle={user ? toggleSidebar : undefined} />
      {user && <Sidebar isOpen={sidebarOpen} />}
      <Content 
        id="main-content" 
        className={user ? styles.pageWithSidebar : styles.pageNoSidebar}
      >
        {children}
      </Content>
    </div>
  );
}
