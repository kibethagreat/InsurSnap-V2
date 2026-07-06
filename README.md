# Micro-Claims Processing Portal

Django front end + rule-based triage engine + Supabase as the data layer.

## Architecture

```
Browser (claim form)
   -> Django view (claims/views.py)
        -> Supabase: fetch policy.active_since   (claims/supabase_client.py)
        -> Triage engine: evaluate_claim(...)     (claims/triage.py, pure function)
        -> Supabase: insert claim + status        (claims/supabase_client.py)
   -> Result page (Auto-Approved / Manual Review)
```

- **claims/triage.py** — the rule engine. Pure Python, no Django/Supabase
  imports, fully unit tested in `claims/tests.py`. This is the single
  source of truth for the auto-approval rule.
- **claims/supabase_client.py** — all Supabase reads/writes go through this
  module. Uses the service-role key server-side only.
- **claims/views.py** — glues the form, the Supabase lookups, and the
  triage engine together.

## Local setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
python manage.py test claims   # run the triage rule tests
python manage.py runserver
```

## Supabase schema

Run in the Supabase SQL editor:

```sql
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

alter table policies enable row level security;
alter table claims enable row level security;
-- No public policies are created: the app talks to Supabase using the
-- service-role key server-side, so RLS stays locked down by default.
```

Seed a test policy so you can submit a claim locally:

```sql
insert into policies (policy_id, active_since) values ('POL-10293', '2025-01-01');
```

## The auto-approval rule

A claim is **Auto-Approved** only if BOTH are true:
1. `claim_amount < AUTO_APPROVAL_MAX_AMOUNT` (default $1,500)
2. Policy age in days `> AUTO_APPROVAL_MIN_POLICY_AGE_DAYS` (default 30)

Otherwise it's routed to **Manual Review**. Both thresholds are environment
variables (`AUTO_APPROVAL_MAX_AMOUNT`, `AUTO_APPROVAL_MIN_POLICY_AGE_DAYS`),
so business can adjust them without a code change or redeploy of the logic
itself — just an env var update and restart.

## Deploying to Render

1. Push this repo to GitHub.
2. In Render, "New +" → "Blueprint" → point at the repo (uses `render.yaml`).
3. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in the Render
   dashboard (marked `sync: false` in render.yaml so they're not committed).
4. Deploy. Render runs `collectstatic` on build and starts gunicorn.

## Security notes

- The Supabase **service-role key** is used, which bypasses Row Level
  Security — it must only ever be read from environment variables on the
  server (Render), never shipped to the browser or committed to git.
- CSRF protection is on by default via Django's middleware; the form uses
  `{% csrf_token %}`.
- Input validation (amount is a positive decimal, category is a fixed
  choice list, Policy ID is required) happens in `claims/forms.py` before
  triage or Supabase ever sees the data.
