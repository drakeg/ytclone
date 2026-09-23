from django.utils import timezone

from ..search_history_models import SearchHistory


SEARCH_HISTORY_LIMIT = 10


def record_search(user, query):
    if not getattr(user, "is_authenticated", False):
        return None

    normalized_query = " ".join((query or "").split())[:255]
    if not normalized_query:
        return None

    existing = SearchHistory.objects.filter(
        user=user,
        query__iexact=normalized_query,
    ).first()
    if existing is not None:
        existing.query = normalized_query
        existing.searched_at = timezone.now()
        existing.save(update_fields=["query", "searched_at"])
        return existing

    return SearchHistory.objects.create(user=user, query=normalized_query)


def recent_searches(user, limit=SEARCH_HISTORY_LIMIT):
    if not getattr(user, "is_authenticated", False) or limit < 1:
        return SearchHistory.objects.none()
    return SearchHistory.objects.filter(user=user).order_by("-searched_at", "-pk")[:limit]


def remove_search_history_entry(user, entry_id):
    if not getattr(user, "is_authenticated", False):
        return 0
    try:
        entry_id = int(entry_id)
    except (TypeError, ValueError):
        return 0
    if entry_id < 1:
        return 0
    deleted, unused = SearchHistory.objects.filter(user=user, pk=entry_id).delete()
    return deleted


def clear_search_history(user):
    if not getattr(user, "is_authenticated", False):
        return 0
    deleted, unused = SearchHistory.objects.filter(user=user).delete()
    return deleted
