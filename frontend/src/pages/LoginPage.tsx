import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, TextInput, InlineNotification, Grid, Column, Stack } from '@carbon/react';
import { useAuth } from '../lib/auth-context';
import styles from './LoginPage.module.scss';

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [loginError, setLoginError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    // Reset errors
    setEmailError('');
    setPasswordError('');
    setLoginError('');

    // Validate
    let hasError = false;
    if (!email.trim()) {
      setEmailError('Enter your username');
      hasError = true;
    }
    if (!password) {
      setPasswordError('Enter your password');
      hasError = true;
    }

    if (hasError) {
      return;
    }

    setIsLoading(true);
    try {
      await login(email, password);
      navigate('/account-overview');
    } catch {
      setLoginError('We could not log you in. Check your username and password, then try again. After 5 failed attempts in 15 minutes, log in is locked for 15 minutes.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.pageContainer}>
      <Grid>
        <Column sm={4} md={8} lg={6}>
          <Stack gap={5}>
            <div>
              <h1 className="cds--type-heading-04">Log in to your credit card account</h1>
              <p className="cds--body-01 cds--spacing-03">
                Enter your username and password to check your balance, make payments and track your requests.
              </p>
            </div>

            {loginError && (
              <InlineNotification
                kind="error"
                title="We could not log you in"
                subtitle={loginError}
                hideCloseButton
                lowContrast
              />
            )}

            <form onSubmit={handleSubmit} className={styles.formContainer}>
              <Stack gap={5}>
                <h2 className="cds--type-heading-03">Log in</h2>
                
                <TextInput
                  id="username"
                  labelText="Username"
                  helperText="The username you use for NBS online banking"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  invalid={!!emailError}
                  invalidText={emailError}
                  disabled={isLoading}
                />

                <TextInput
                  id="password"
                  type="password"
                  labelText="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  invalid={!!passwordError}
                  invalidText={passwordError}
                  disabled={isLoading}
                />

                <Button type="submit" disabled={isLoading}>
                  {isLoading ? 'Logging in...' : 'Log in'}
                </Button>
              </Stack>
            </form>

            <p className={`cds--label-01 ${styles.helperText}`}>
              You will be logged out after 15 minutes of inactivity. If you cannot log in, contact support. Marketing preferences never affect access to servicing.
            </p>
          </Stack>
        </Column>

        <Column sm={4} md={8} lg={8}>
          <Stack gap={5}>
            <div className={styles.sectionContainer}>
              <h2 className={`cds--type-heading-02 ${styles.sectionHeading}`}>
                What you can do once you are in
              </h2>
              <ul className={styles.listContainer}>
                <li className={styles.listItem}>See your balance, available credit, payment due date and minimum payment</li>
                <li className={styles.listItem}>Understand what makes up your balance, including promotional and balance transfer amounts</li>
                <li className={styles.listItem}>Make a payment, review payment history and check your direct debit</li>
                <li className={styles.listItem}>Request a balance transfer or a money transfer</li>
                <li className={styles.listItemLast}>Track every request in one place and see how fresh the information is</li>
              </ul>
            </div>

            <div className={styles.sectionContainer}>
              <h2 className={`cds--type-heading-02 ${styles.sectionHeadingSmall}`}>
                Keeping your account secure
              </h2>
              <p className="cds--body-01">
                We show only the last digits of card, sort code and account numbers. Some actions, such as payments and transfers, ask you to confirm your identity again before they go ahead.
              </p>
            </div>
          </Stack>
        </Column>
      </Grid>
    </div>
  );
}
