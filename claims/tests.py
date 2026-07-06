from datetime import date, timedelta
from decimal import Decimal

from django.test import SimpleTestCase

from .triage import ClaimStatus, TriageError, evaluate_claim


class EvaluateClaimTests(SimpleTestCase):
    TODAY = date(2026, 7, 4)

    def test_auto_approved_when_under_limit_and_policy_old_enough(self):
        active_since = self.TODAY - timedelta(days=31)
        result = evaluate_claim(1499.99, active_since, as_of=self.TODAY)
        self.assertEqual(result.status, ClaimStatus.AUTO_APPROVED)
        self.assertTrue(result.is_auto_approved)

    def test_manual_review_when_amount_at_or_over_limit(self):
        active_since = self.TODAY - timedelta(days=60)
        result = evaluate_claim(1500.00, active_since, as_of=self.TODAY)
        self.assertEqual(result.status, ClaimStatus.MANUAL_REVIEW)

    def test_manual_review_when_policy_too_new(self):
        active_since = self.TODAY - timedelta(days=30)  # exactly 30, must be > 30
        result = evaluate_claim(500.00, active_since, as_of=self.TODAY)
        self.assertEqual(result.status, ClaimStatus.MANUAL_REVIEW)

    def test_manual_review_when_policy_active_since_today(self):
        result = evaluate_claim(100.00, self.TODAY, as_of=self.TODAY)
        self.assertEqual(result.status, ClaimStatus.MANUAL_REVIEW)

    def test_manual_review_when_both_conditions_fail(self):
        active_since = self.TODAY - timedelta(days=5)
        result = evaluate_claim(5000.00, active_since, as_of=self.TODAY)
        self.assertEqual(result.status, ClaimStatus.MANUAL_REVIEW)
        self.assertEqual(len(result.reasons), 2)

    def test_custom_thresholds_are_respected(self):
        active_since = self.TODAY - timedelta(days=10)
        result = evaluate_claim(
            2000.00,
            active_since,
            auto_approval_max_amount=Decimal("2500.00"),
            min_policy_age_days=5,
            as_of=self.TODAY,
        )
        self.assertEqual(result.status, ClaimStatus.AUTO_APPROVED)

    def test_negative_amount_raises(self):
        with self.assertRaises(TriageError):
            evaluate_claim(-1, self.TODAY - timedelta(days=40), as_of=self.TODAY)

    def test_non_numeric_amount_raises(self):
        with self.assertRaises(TriageError):
            evaluate_claim("not-a-number", self.TODAY - timedelta(days=40), as_of=self.TODAY)
