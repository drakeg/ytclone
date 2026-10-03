from dataclasses import dataclass

from django.db.models import Q, Sum

from .models import MonetizationTransaction


@dataclass(frozen=True)
class PayoutReadinessSummary:
    earned_minor: int
    pending_minor: int
    refunded_reversed_minor: int
    paid_out_minor: int
    available_minor: int


def _amount(value):
    return int(value or 0)


def payout_readiness_summary(account):
    transactions = account.transactions

    earned = _amount(
        transactions.filter(
            status=MonetizationTransaction.Status.SUCCEEDED,
            kind__in=[
                MonetizationTransaction.Kind.TIP,
                MonetizationTransaction.Kind.MEMBERSHIP,
            ],
        ).aggregate(total=Sum("creator_net_minor"))["total"]
    )
    pending = _amount(
        transactions.filter(
            status=MonetizationTransaction.Status.PENDING,
            kind__in=[
                MonetizationTransaction.Kind.TIP,
                MonetizationTransaction.Kind.MEMBERSHIP,
            ],
        ).aggregate(total=Sum("creator_net_minor"))["total"]
    )
    refunded_reversed_net = _amount(
        transactions.filter(
            status=MonetizationTransaction.Status.SUCCEEDED,
            kind__in=[
                MonetizationTransaction.Kind.REFUND,
                MonetizationTransaction.Kind.REVERSAL,
            ],
            creator_net_minor__lt=0,
        ).aggregate(total=Sum("creator_net_minor"))["total"]
    )
    paid_out_net = _amount(
        transactions.filter(
            status=MonetizationTransaction.Status.SUCCEEDED,
            kind=MonetizationTransaction.Kind.PAYOUT,
            creator_net_minor__lt=0,
        ).aggregate(total=Sum("creator_net_minor"))["total"]
    )
    available = _amount(
        transactions.filter(
            status=MonetizationTransaction.Status.SUCCEEDED,
        ).aggregate(total=Sum("creator_net_minor"))["total"]
    )

    return PayoutReadinessSummary(
        earned_minor=earned,
        pending_minor=pending,
        refunded_reversed_minor=abs(refunded_reversed_net),
        paid_out_minor=abs(paid_out_net),
        available_minor=available,
    )
