# Creator Payout Readiness Summary Sprint

## Goal

Show creators a payout-readiness accounting summary derived entirely from the existing monetization ledger, without initiating or scheduling any payout.

## Scope

- Add a reusable ledger-summary service for a creator monetization account.
- Derive and display:
  - earned creator net from succeeded tips and memberships
  - pending creator net from pending tips and memberships
  - refunded/reversed creator net
  - paid-out creator net represented by succeeded payout ledger entries
  - currently available creator balance
- Keep the creator dashboard owner-only through its existing channel ownership guard.
- Define the payout ledger convention for future integrations: a completed payout records the transferred amount as a `PAYOUT` transaction with negative `creator_net_minor`; no payout API is added in this sprint.
- Keep all calculations in integer minor units.
- Add focused regression coverage for mixed payment, refund, pending, failed, and payout ledger entries.

## Accounting rules

For a single monetization account:

- **Earned** = succeeded `TIP` + `MEMBERSHIP` creator-net amounts.
- **Pending** = pending `TIP` + `MEMBERSHIP` creator-net amounts.
- **Refunded/reversed** = absolute value of negative creator-net amounts on succeeded `REFUND` + `REVERSAL` entries.
- **Paid out** = absolute value of negative creator-net amounts on succeeded `PAYOUT` entries.
- **Available** = sum of `creator_net_minor` across all succeeded ledger entries.

Failed transactions never affect balances.

## Acceptance criteria

1. Dashboard balances are derived from ledger entries rather than a mutable stored balance.
2. Refunds/reversals reduce available funds.
3. Payout ledger entries reduce available funds.
4. Pending and failed entries do not inflate available funds.
5. No live payout, Stripe transfer, provider API call, worker, scheduler, AWS resource, or paid service is introduced.
6. No schema or migration is required.
7. Existing Stripe test-mode/live-key safety gates remain unchanged.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test monetization.tests monetization.test_stripe_accounting
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

## Out of scope

- Creating or scheduling payouts
- Stripe payout/transfer API calls
- Bank-account management
- Provider balance synchronization
- Payout approval workflows
- Live-mode activation
- Tax reporting
