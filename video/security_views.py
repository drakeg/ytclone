from urllib.parse import urlencode

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


CSRF_FAILURE_MESSAGE = "That form expired for security reasons. Please try again."


def csrf_failure(request, reason=""):
    """Recover from stale/invalid CSRF submissions without exposing Django's 403 page."""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "error": "csrf_failed",
                "message": CSRF_FAILURE_MESSAGE,
            },
            status=403,
        )

    referer = request.META.get("HTTP_REFERER", "")
    safe_referer = referer if url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ) else ""

    messages.warning(request, CSRF_FAILURE_MESSAGE)

    # Login rotates Django's CSRF token. A stale login form is the most common
    # place users encounter this, so issue a fresh login page and preserve the
    # requested destination when it is safe.
    if request.path == reverse("login"):
        next_url = request.POST.get("next", "")
        login_url = reverse("login")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            login_url = f"{login_url}?{urlencode({'next': next_url})}"
        return redirect(login_url)

    # For other stale forms, return the user to the page the form came from so
    # it can render a fresh CSRF token. Never redirect to an untrusted origin.
    if safe_referer:
        return redirect(safe_referer)
    return redirect("video_list")
