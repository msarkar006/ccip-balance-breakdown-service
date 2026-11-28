import { useState, type FormEvent } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Accordion, AccordionItem, Button, Content, Form, Header, HeaderName, InlineNotification, PasswordInput, SkipToContent, Stack, TextInput } from '@carbon/react';
import { ArrowRight } from '@carbon/icons-react';
import { ApiError } from '../lib/api-client';
import { useAuth } from '../lib/auth-context';
import { BoundaryBanner } from '../components/layout/BoundaryBanner';

interface Failure {
  kind: 'failed' | 'throttled' | 'unavailable';
  detail: string;
}

export default function LoginPage() {
  const { status, login, sessionEnded } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [touched, setTouched] = useState(false);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);

  if (status === 'authenticated') {
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={from && from !== '/login' ? from : '/accounts'} replace />;
  }

  const userMissing = touched && username.trim() === '';
  const passMissing = touched && password === '';

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setTouched(true);
    if (username.trim() === '' || password === '') return;
    setBusy(true);
    setFailure(null);
    try {
      await login({ username: username.trim(), password });
    } catch (error) {
      if (error instanceof ApiError && error.status === 429) {
        setFailure({ kind: 'throttled', detail: 'Sign-in is paused for a short time after repeated failed attempts. Try again later.' });
      } else if (error instanceof ApiError && error.status === 401) {
        setFailure({ kind: 'failed', detail: 'The username or password was not accepted. Check the details and try again.' });
      } else {
        setFailure({ kind: 'unavailable', detail: error instanceof ApiError ? error.detail : 'Something went wrong. Try again later.' });
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Header aria-label="Credit card information prototype">
        <SkipToContent href="#main-content">Skip to main content</SkipToContent>
        <HeaderName href="/login" prefix="Prototype">
          Card information
        </HeaderName>
      </Header>
      <Content id="main-content" className="login-content">
        <div className="login-panel">
          <h1 className="page-title">Sign in</h1>
          <p className="page-lead">Sign in to view synthetic credit card information. This prototype is read-only.</p>
          <BoundaryBanner />
          <InlineNotification
            role="status"
            kind="info"
            lowContrast
            hideCloseButton
            title="Information only"
            subtitle="You can view account, balance, transaction and payment information. You cannot make payments or changes here."
          />
          {sessionEnded && !failure ? (
            <InlineNotification
              role="status"
              kind="info"
              lowContrast
              hideCloseButton
              title="You have been signed out"
              subtitle="Your session ended because you signed out or were inactive. Sign in again to continue."
            />
          ) : null}
          {failure ? (
            <InlineNotification
              role="alert"
              kind={failure.kind === 'throttled' ? 'warning' : 'error'}
              lowContrast
              hideCloseButton
              title={failure.kind === 'throttled' ? 'Too many sign-in attempts' : failure.kind === 'failed' ? 'Sign-in failed' : 'Sign-in unavailable'}
              subtitle={failure.detail}
            />
          ) : null}
          <Form onSubmit={onSubmit} noValidate aria-labelledby="signin-heading">
            <Stack gap={6}>
              <h2 id="signin-heading" className="section-title">
                Your sign-in details
              </h2>
              <TextInput
                id="username"
                name="username"
                labelText="Username"
                autoComplete="username"
                helperText="Use the synthetic demonstration username you were given."
                value={username}
                invalid={userMissing}
                invalidText="Enter your username."
                onChange={(event) => setUsername(event.target.value)}
              />
              <PasswordInput
                id="password"
                name="password"
                labelText="Password"
                showPasswordLabel="Show"
                hidePasswordLabel="Hide"
                autoComplete="current-password"
                value={password}
                invalid={passMissing}
                invalidText="Enter your password."
                onChange={(event) => setPassword(event.target.value)}
              />
              <Button type="submit" size="lg" renderIcon={ArrowRight} disabled={busy}>
                Sign in
              </Button>
              <p className="helper-text">Your session ends after a period of inactivity and when you sign out.</p>
            </Stack>
          </Form>
          <Accordion className="design-notes">
            <AccordionItem title="Design notes for this wireframe">
              <ul>
                <li><strong>Safe errors:</strong> messages never say whether the username or the password was wrong, and never show tokens or credentials.</li>
                <li><strong>Session:</strong> your session ends after a period of inactivity and when you sign out. Authentication is access control, not a financial action.</li>
              </ul>
            </AccordionItem>
          </Accordion>
        </div>
      </Content>
    </>
  );
}
