"""
Core claim triage rule engine.

Deliberately framework-agnostic: no Django imports, no Supabase imports,
no I/O. It takes plain values in and returns a plain result out, so it can
be unit tested in isolation and reused from a view, a management command,
a Celery task, or a serverless function without modification.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum


class ClaimStatus(str, Enum):
    AUTO_APPROVED = "Auto-Approved"
    MANUAL_REVIEW = "Manual Review"


@dataclass(frozen=True)
class TriageResult:
    status: ClaimStatus
    reasons: list[str]

    @property
    def is_auto_approved(self) -> bool:
        return self.status is ClaimStatus.AUTO_APPROVED


class TriageError(ValueError):
    """Raised when triage inputs are structurally invalid (not a business decline)."""


def _coerce_amount(claim_amount) -> Decimal:
    try:
        amount = Decimal(str(claim_amount))
    except (InvalidOperation, TypeError) as exc:
        raise TriageError(f"Claim amount '{claim_amount}' is not a valid decimal number.") from exc
    if amount < 0:
        raise TriageError("Claim amount cannot be negative.")
    return amount


def _policy_age_days(policy_active_since: date, as_of: date | None = None) -> int:
    as_of = as_of or date.today()
    if isinstance(policy_active_since, datetime):
        policy_active_since = policy_active_since.date()
    return (as_of - policy_active_since).days


def evaluate_claim(
    claim_amount,
    policy_active_since: date,
    *,
    auto_approval_max_amount=Decimal("1500.00"),
    min_policy_age_days: int = 30,
    as_of: date | None = None,
) -> TriageResult:
    """
    Apply the auto-approval rule:

        Auto-Approved  <=>  claim_amount < auto_approval_max_amount
                             AND policy_age_days > min_policy_age_days

    Anything that doesn't satisfy both conditions is routed to manual review.
    Both thresholds are parameters (not hardcoded) so they can be tuned via
    Django settings/environment variables without touching this function.
    """
    amount = _coerce_amount(claim_amount)
    max_amount = _coerce_amount(auto_approval_max_amount)
    age_days = _policy_age_days(policy_active_since, as_of=as_of)

    reasons = []
    amount_ok = amount < max_amount
    age_ok = age_days > min_policy_age_days

    if not amount_ok:
        reasons.append(
            f"Claim amount {amount} is not under the auto-approval limit of {max_amount}."
        )
    if not age_ok:
        reasons.append(
            f"Policy has been active for {age_days} day(s); "
            f"requires more than {min_policy_age_days}."
        )

    if amount_ok and age_ok:
        return TriageResult(status=ClaimStatus.AUTO_APPROVED, reasons=["Meets auto-approval criteria."])

    return TriageResult(status=ClaimStatus.MANUAL_REVIEW, reasons=reasons)
