import { Modal, TextInput, InlineNotification } from '@carbon/react';
import { useState } from 'react';
import { apiClient } from '../../lib/api-client';
import styles from './StepUpModal.module.scss';

interface StepUpModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (token: string) => void;
  scope?: string;
}

export function StepUpModal({ open, onClose, onSuccess, scope = 'payment' }: StepUpModalProps) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await apiClient.post<{ success: boolean; message: string; valid_until: string }>(
        '/v1/auth/step-up',
        { password }
      );

      if (response.success) {
        // Generate a proof token for step-up (in production, this would be a real JWT from backend)
        const proofToken = `step-up-${scope}-${Date.now()}`;
        onSuccess(proofToken);
        setPassword('');
        onClose();
      } else {
        setError(response.message || 'Step-up verification failed');
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Step-up verification failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setPassword('');
    setError('');
    onClose();
  };

  return (
    <Modal
      open={open}
      modalHeading="Verify your identity"
      primaryButtonText="Verify and continue"
      secondaryButtonText="Cancel"
      onRequestClose={handleClose}
      onRequestSubmit={handleSubmit}
      primaryButtonDisabled={isLoading || !password}
    >
      <p className={styles.modalContent}>
        For your security, please re-enter your password to confirm this action.
      </p>
      {error && (
        <InlineNotification
          kind="error"
          title="Verification failed"
          subtitle={error}
          lowContrast
          hideCloseButton
          className={styles.notification}
        />
      )}
      <form onSubmit={handleSubmit}>
        <TextInput
          id="step-up-password"
          labelText="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isLoading}
          autoComplete="current-password"
        />
      </form>
    </Modal>
  );
}
