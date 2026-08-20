from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from stripe import StripeClient


class StripeConfigurationError(RuntimeError):
    pass


def _client() -> StripeClient:
    key = settings.STRIPE_SECRET_KEY
    if not key:
        raise StripeConfigurationError("Stripe test-mode secret key is not configured.")
    if not key.startswith("sk_test_"):
        raise StripeConfigurationError("Only Stripe test-mode secret keys are allowed.")
    return StripeClient(key)


def stripe_enabled() -> bool:
    return settings.MONETIZATION_PAYMENT_PROVIDER == "stripe"


def platform_fee_amount(gross_minor: int) -> int:
    return (gross_minor * settings.MONETIZATION_PLATFORM_FEE_BPS) // 10000


def platform_fee_percent() -> float:
    return settings.MONETIZATION_PLATFORM_FEE_BPS / 100


@dataclass(frozen=True)
class CheckoutTarget:
    url: str
    session_id: str


def create_connected_account(*, email: str | None = None) -> str:
    params = {"type": "express"}
    if email:
        params["email"] = email
    account = _client().v1.accounts.create(params)
    return account.id


def create_account_onboarding_link(*, account_id: str, refresh_url: str, return_url: str) -> str:
    link = _client().v1.account_links.create(
        {
            "account": account_id,
            "refresh_url": refresh_url,
            "return_url": return_url,
            "type": "account_onboarding",
        }
    )
    return link.url


def retrieve_connected_account(account_id: str):
    return _client().v1.accounts.retrieve(account_id)


def create_tip_checkout(*, connected_account_id: str, amount_minor: int, channel_name: str, payer_id: int, channel_id: int, success_url: str, cancel_url: str) -> CheckoutTarget:
    fee_minor = platform_fee_amount(amount_minor)
    session = _client().v1.checkout.sessions.create(
        {
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "submit_type": "donate",
            "line_items": [
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_minor,
                        "product_data": {"name": f"Tip for {channel_name}"},
                    },
                }
            ],
            "payment_intent_data": {
                "application_fee_amount": fee_minor,
                "transfer_data": {"destination": connected_account_id},
                "metadata": {
                    "ytclone_kind": "tip",
                    "ytclone_channel_id": str(channel_id),
                    "ytclone_payer_id": str(payer_id),
                },
            },
            "metadata": {
                "ytclone_kind": "tip",
                "ytclone_channel_id": str(channel_id),
                "ytclone_payer_id": str(payer_id),
                "ytclone_gross_minor": str(amount_minor),
                "ytclone_platform_fee_minor": str(fee_minor),
            },
        }
    )
    return CheckoutTarget(url=session.url, session_id=session.id)


def create_membership_checkout(*, connected_account_id: str, tier_id: int, tier_name: str, price_minor: int, channel_id: int, payer_id: int, success_url: str, cancel_url: str) -> CheckoutTarget:
    session = _client().v1.checkout.sessions.create(
        {
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items": [
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": price_minor,
                        "recurring": {"interval": "month"},
                        "product_data": {"name": tier_name},
                    },
                }
            ],
            "subscription_data": {
                "application_fee_percent": platform_fee_percent(),
                "transfer_data": {"destination": connected_account_id},
                "metadata": {
                    "ytclone_kind": "membership",
                    "ytclone_tier_id": str(tier_id),
                    "ytclone_channel_id": str(channel_id),
                    "ytclone_payer_id": str(payer_id),
                },
            },
            "metadata": {
                "ytclone_kind": "membership",
                "ytclone_tier_id": str(tier_id),
                "ytclone_channel_id": str(channel_id),
                "ytclone_payer_id": str(payer_id),
            },
        }
    )
    return CheckoutTarget(url=session.url, session_id=session.id)


def cancel_membership_at_period_end(provider_subscription_id: str):
    return _client().v1.subscriptions.update(
        provider_subscription_id,
        {"cancel_at_period_end": True},
    )


def construct_webhook_event(payload: bytes, signature: str):
    secret = settings.STRIPE_WEBHOOK_SECRET
    if not secret:
        raise StripeConfigurationError("Stripe webhook signing secret is not configured.")
    return _client().construct_event(payload, signature, secret)


def refund_destination_charge(*, charge_id: str, amount_minor: int | None = None):
    params = {
        "charge": charge_id,
        "reverse_transfer": True,
        "refund_application_fee": True,
    }
    if amount_minor is not None:
        params["amount"] = amount_minor
    return _client().v1.refunds.create(params)
