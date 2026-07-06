"""
Thin wrapper around the Supabase Python client.

Expected Supabase schema (create these tables in the Supabase SQL editor):

    create table policies (
        policy_id text primary key,
        active_since date not null,
        status text not null default 'active'
    );

    create table claims (
        id uuid primary key default gen_random_uuid(),
        policy_id text references policies(policy_id),
        claim_amount numeric not null,
        loss_category text not null,
        status text not null,
        triage_reasons text,
        created_at timestamptz not null default now()
    );

The service-role key is used server-side only (never exposed to the
browser) so Row Level Security can stay strict on these tables.
"""

from datetime import date
from functools import lru_cache

from django.conf import settings
from supabase import Client, create_client


class SupabaseConfigError(RuntimeError):
    """Raised when Supabase credentials are missing or invalid."""


class PolicyNotFoundError(LookupError):
    """Raised when a Policy ID does not exist in Supabase."""


@lru_cache(maxsize=1)
def get_client() -> Client:
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not url or not key:
        raise SupabaseConfigError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set as environment variables."
        )
    return create_client(url, key)


def fetch_policy_active_since(policy_id: str) -> date:
    """Look up a policy's activation date by Policy ID. Raises PolicyNotFoundError if absent."""
    client = get_client()
    response = (
        client.table("policies")
        .select("active_since")
        .eq("policy_id", policy_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise PolicyNotFoundError(f"No policy found with Policy ID '{policy_id}'.")

    raw_date = response.data[0]["active_since"]
    return date.fromisoformat(raw_date) if isinstance(raw_date, str) else raw_date


def insert_claim(
    *,
    policy_id: str,
    claim_amount,
    loss_category: str,
    status: str,
    triage_reasons: str,
) -> dict:
    """Persist a submitted claim and its triage outcome. Returns the inserted row."""
    client = get_client()
    payload = {
        "policy_id": policy_id,
        "claim_amount": str(claim_amount),
        "loss_category": loss_category,
        "status": status,
        "triage_reasons": triage_reasons,
    }
    response = client.table("claims").insert(payload).execute()
    return response.data[0]
