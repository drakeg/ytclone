# Monetization and Memberships

## Scope

Creators can enable a monetization account, define monthly membership tiers,
accept tips, and publish members-only videos. The built-in sandbox supports local
product testing without external payment calls. Stripe integration is restricted
to test-mode keys and supports test checkouts, recurring invoice events,
cancellation state, refunds, and creator/platform accounting.

An active paid membership unlocks members-only videos for its channel. Free
channel subscriptions do not. A Stripe viewer must cancel an existing channel
membership before selecting another tier; automatic provider-side tier switching
is not implemented.

## Stripe test mode

Set the payment provider and Stripe test credentials in `.env`. Never commit
credentials and never use a live secret key with this application.

```text
MONETIZATION_PAYMENT_PROVIDER=stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Forward Stripe test events to the webhook route exposed by the locally configured
Compose port. The Stripe CLI prints the webhook signing secret needed above.

```bash
stripe listen --forward-to localhost:8000/monetization/stripe/webhook/
```

If `APP_PORT` changes the host port, use that value instead of `8000`.

## Accounting guarantees

- Every provider event uses a unique event identifier for idempotency.
- Stripe's cumulative partial-refund amount is converted into an incremental
  ledger entry, preventing earlier refunds from being counted twice.
- Platform-fee reversals are accumulated proportionally to the total refund.
- Failed recurring invoices do not contribute creator or platform revenue.

## Local verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test monetization
python manage.py test
```

Or run all required checks in containers:

```bash
docker compose run --build --rm test
```

Stripe credentials are not required for the automated test suite.
