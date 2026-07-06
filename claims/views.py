import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.html import escape

try:
    import markdown as _markdown
except ImportError:  # pragma: no cover - exercised only if the dependency is missing
    _markdown = None

from .forms import ClaimSubmissionForm
from .supabase_client import (
    PolicyNotFoundError,
    SupabaseConfigError,
    fetch_policy_active_since,
    insert_claim,
)
from .triage import evaluate_claim

logger = logging.getLogger(__name__)


def landing(request):
    """Public marketing landing page."""
    return render(request, "claims/landing.html")


def claim_submit(request):
    """Render the claim intake form and process submissions."""
    if request.method == "POST":
        form = ClaimSubmissionForm(request.POST)
        if form.is_valid():
            policy_id = form.cleaned_data["policy_id"]
            claim_amount = form.cleaned_data["claim_amount"]
            loss_category = form.cleaned_data["loss_category"]

            try:
                active_since = fetch_policy_active_since(policy_id)
            except PolicyNotFoundError:
                form.add_error("policy_id", "We couldn't find that Policy ID. Please check and try again.")
                return render(request, "claims/claim_form.html", {"form": form})
            except SupabaseConfigError:
                logger.exception("Supabase is not configured.")
                messages.error(request, "The claims service is temporarily unavailable. Please try again shortly.")
                return render(request, "claims/claim_form.html", {"form": form})

            result = evaluate_claim(
                claim_amount,
                active_since,
                auto_approval_max_amount=settings.AUTO_APPROVAL_MAX_AMOUNT,
                min_policy_age_days=settings.AUTO_APPROVAL_MIN_POLICY_AGE_DAYS,
            )

            try:
                saved_claim = insert_claim(
                    policy_id=policy_id,
                    claim_amount=claim_amount,
                    loss_category=loss_category,
                    status=result.status.value,
                    triage_reasons="; ".join(result.reasons),
                )
            except SupabaseConfigError:
                logger.exception("Supabase is not configured.")
                messages.error(request, "The claims service is temporarily unavailable. Please try again shortly.")
                return render(request, "claims/claim_form.html", {"form": form})

            request.session["last_claim"] = {
                "policy_id": policy_id,
                "claim_amount": str(claim_amount),
                "loss_category": loss_category,
                "status": result.status.value,
                "reasons": result.reasons,
                "record_id": saved_claim.get("id"),
            }
            return redirect("claim_result")
    else:
        form = ClaimSubmissionForm()

    return render(request, "claims/claim_form.html", {"form": form})


def how_it_works(request):
    """Render the project README as a styled 'How it Works' page."""
    readme_path = settings.BASE_DIR / "README.md"

    try:
        readme_text = readme_path.read_text(encoding="utf-8")
    except OSError:
        logger.exception("Could not read README.md at %s", readme_path)
        readme_html = "<p>Documentation is temporarily unavailable.</p>"
    else:
        if _markdown is not None:
            readme_html = _markdown.markdown(
                readme_text,
                extensions=["fenced_code", "tables", "sane_lists"],
            )
        else:
            # Fallback so the page still renders something useful even if
            # the `markdown` package isn't installed yet.
            logger.warning("`markdown` package not installed; rendering README.md as plain text.")
            readme_html = f"<pre>{escape(readme_text)}</pre>"

    return render(request, "claims/how_it_works.html", {"readme_html": readme_html})


def claim_result(request):
    """Show the outcome of the most recently submitted claim in this session."""
    claim = request.session.get("last_claim")
    if not claim:
        return redirect("claim_submit")
    return render(request, "claims/claim_result.html", {"claim": claim})
