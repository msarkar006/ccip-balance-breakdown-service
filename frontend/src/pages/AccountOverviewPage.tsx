import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import { InlineLoading, InlineNotification, Link, Select, SelectItem } from '@carbon/react';
import { useAccount, useAccounts, useCards } from '../lib/queries';
import { ErrorNotice } from '../components/common/ErrorNotice';
import { AccountSummary } from '../components/account/AccountSummary';
import { CardList } from '../components/account/CardList';
import '../components/account/account.css';

function AccountUnavailable({ error }: { error: unknown }) {
  return (
    <div>
      <ErrorNotice error={error} title="Account information is unavailable" />
      <p className="account-helper">The account record could not be shown. No value is estimated.</p>
      <p>
        <Link as={RouterLink} to="/data-status">
          Data status and limitations
        </Link>
      </p>
    </div>
  );
}

/** One account opens directly; several show a switcher. Values come from the account and cards endpoints. */
export default function AccountOverviewPage() {
  const { accountId } = useParams();
  const navigate = useNavigate();
  const list = useAccounts({ limit: 100 });
  const items = list.data?.items ?? [];
  const id = accountId ?? items[0]?.id;
  const account = useAccount(id);
  const cards = useCards(id);
  const loading = list.loading || (id !== undefined && account.loading);

  let body;
  if (list.error || account.error) {
    body = <AccountUnavailable error={list.error ?? account.error} />;
  } else if (loading) {
    body = <InlineLoading status="active" description="Loading account information" role="status" />;
  } else if (!account.data) {
    body = (
      <InlineNotification
        kind="info"
        lowContrast
        hideCloseButton
        title="No account is available"
        subtitle="No account is held for this sign-in."
      />
    );
  } else {
    body = (
      <>
        {items.length > 1 ? (
          <div className="account-switcher">
            <Select
              id="account-switcher"
              labelText="Account"
              value={id}
              onChange={(event: React.ChangeEvent<HTMLSelectElement>) => navigate(`/accounts/${event.target.value}`)}
            >
              {items.map((item) => (
                <SelectItem key={item.id} value={item.id} text={`${item.productName} (${item.sourceRef ?? item.id})`} />
              ))}
            </Select>
          </div>
        ) : null}
        <AccountSummary account={account.data} />
        {cards.error ? (
          <ErrorNotice error={cards.error} title="Card information is unavailable" />
        ) : cards.loading ? (
          <InlineLoading status="active" description="Loading card information" role="status" />
        ) : (
          <CardList cards={cards.data?.items ?? []} />
        )}
        <p>
          <Link as={RouterLink} to={`/accounts/${account.data.id}/balance`}>
            View dated balance breakdown
          </Link>
        </p>
      </>
    );
  }

  return (
    <section aria-labelledby="page-heading">
      <h1 id="page-heading" className="page-title">
        Account overview
      </h1>
      {account.data ? (
        <p className="page-lead">
          Credit card account <span className="mono">{account.data.sourceRef ?? account.data.id}</span>. This screen shows
          information only. It has no payment, card or account actions.
        </p>
      ) : null}
      {body}
    </section>
  );
}
