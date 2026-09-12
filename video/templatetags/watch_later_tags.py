from django import template

from video.services.watch_later import is_saved_for_later


register = template.Library()


@register.inclusion_tag("videos/_watch_later_action.html", takes_context=True)
def watch_later_action(context, video):
    request = context.get("request")
    user = getattr(request, "user", None)
    return {
        "video": video,
        "request": request,
        "saved_for_later": bool(user and user.is_authenticated and is_saved_for_later(user, video)),
    }
