import { Tile, Tag, Button, Stack } from '@carbon/react';
import { Link } from 'react-router-dom';
import type { Offer } from '../../types/rewards';
import styles from './OfferList.module.scss';

interface OfferListProps {
  offers: Offer[];
}

export function OfferList({ offers }: OfferListProps) {
  if (offers.length === 0) {
    return (
      <p className={styles.empty}>No offers available for this account at the moment.</p>
    );
  }

  return (
    <ul className={styles.offerGrid}>
      {offers.map((offer) => (
        <li key={offer.id}>
          <Tile className={styles.offerCard}>
            <Stack gap={4}>
              <div className={styles.tags}>
                <Tag type="blue" size="sm">{offer.offer_type}</Tag>
                <Tag type="green" size="sm">{offer.status}</Tag>
              </div>
              
              <h3 className={styles.offerTitle}>{offer.offer_title}</h3>
              
              <p className={styles.offerDescription}>{offer.offer_description}</p>
              
              {offer.offer_type === 'BalanceTransfer' && (
                <div className={styles.actions}>
                  <Button as={Link} to="/transfers" kind="tertiary" size="sm">
                    Request a balance transfer
                  </Button>
                </div>
              )}
            </Stack>
          </Tile>
        </li>
      ))}
    </ul>
  );
}
