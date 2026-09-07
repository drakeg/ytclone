from django import template

from video.services.recommendations import watch_recommendations


register = template.Library()


@register.inclusion_tag("videos/_watch_recommendations.html", takes_context=True)
def watch_recommendations_for(context, video):
    request = context["request"]
    return {"recommendations": watch_recommendations(video, request.user)}
