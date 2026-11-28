import { Tile } from '@carbon/react';
import { LabelledValue } from '../common/LabelledValue';
import { StatusTag } from '../common/StatusTag';
import { formatExpiry, formatYesNo } from '../../lib/format';
import type { Card } from '../../types/account';
import './account.css';

function cardHelper(status: string): string {
  if (status === 'Active') {
    return 'Only the masked card reference is held. An Active status is source context and does not show that the card can be used or changed here.';
  }
  return 'The source status is shown exactly as supplied. This prototype offers no activation control and makes no statement about when the card could be activated.';
}

/** One tile per card. The card status is printed exactly as the source supplied it. */
export function CardList({ cards }: { cards: Card[] }) {
  if (cards.length === 0) {
    return (
      <Tile className="account-tile">
        <h2 className="account-tile__title">Card on this account</h2>
        <p className="account-helper">No card is held for this account.</p>
      </Tile>
    );
  }
  return (
    <>
      {cards.map((card) => (
        <Tile key={card.id} className="account-tile" aria-labelledby={`card-h-${card.id}`}>
          <div className="account-tile__head">
            <div>
              <h2 className="account-tile__title" id={`card-h-${card.id}`}>
                Card on this account
              </h2>
              <p className="account-helper">
                Card <span className="mono">{card.sourceRef ?? card.id}</span>
              </p>
            </div>
            <StatusTag status={`Card status: ${card.cardStatus}`} />
          </div>
          <dl className="account-kvs">
            <LabelledValue label="Card number (masked)" value={<span className="mono">{card.maskedPan}</span>} />
            <LabelledValue label="Expiry" value={formatExpiry(card.expiryMonthYear)} />
            <LabelledValue label="Digital card" value={formatYesNo(card.isDigital)} />
          </dl>
          <p className="account-helper">{cardHelper(card.cardStatus)}</p>
        </Tile>
      ))}
    </>
  );
}
