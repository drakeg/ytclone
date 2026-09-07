from django import template

from video.services.recommendations import watch_recommendations


register = template.Library()


@register.simple_tag(takes_context=True)
def watch_recommendations_for(context, video):
    request = context["request"]
    return watch_recommendations(video, request.user)
