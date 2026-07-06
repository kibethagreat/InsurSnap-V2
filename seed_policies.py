"""
Seeds a couple of test policies into Supabase so you can submit claims
against them locally. Uses the same get_client() the app uses, so it
relies on SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY already being set
(e.g. in your .env file).

Usage:
    python seed_policies.py
"""

import os
from datetime import date, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "claims_portal.settings")
import django

django.setup()

from claims.supabase_client import get_client  # noqa: E402

TEST_POLICIES = [
    # policy_id, active_since -> use case
    ("POL-10293", date.today() - timedelta(days=90)),  # old enough -> can auto-approve
    ("POL-BRANDNEW", date.today()),                     # too new -> always manual review
]


def main():
    client = get_client()
    for policy_id, active_since in TEST_POLICIES:
        payload = {
            "policy_id": policy_id,
            "active_since": active_since.isoformat(),
            "status": "active",
        }
        # upsert so re-running this script is safe / idempotent
        response = client.table("policies").upsert(payload, on_conflict="policy_id").execute()
        print(f"Seeded {policy_id} (active_since={active_since}) -> {response.data}")


if __name__ == "__main__":
    main()
