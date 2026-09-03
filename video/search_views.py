from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .services.search import search_suggestions


@require_GET
def suggestions(request):
    return JsonResponse(
        {"suggestions": search_suggestions(request.GET.get("query", ""), request.user)}
    )
