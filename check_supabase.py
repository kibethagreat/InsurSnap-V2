import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "claims_portal.settings")
import django
django.setup()

from claims.supabase_client import get_client, SupabaseConfigError

try:
    client = get_client()
    print("Client created OK. Trying a query against 'policies'...")
    resp = client.table("policies").select("*").limit(1).execute()
    print("Query succeeded:", resp.data)
except SupabaseConfigError as e:
    print("Config error (expected if env vars aren't set):", e)
except Exception as e:
    print("Other error:", type(e).__name__, e)
