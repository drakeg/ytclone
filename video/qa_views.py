from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .forms import CommentForm
from .models import Comment, Video
from .qa_models import VideoQuestion
from .services.notifications import notify_comment


@login_required
@require_POST
def ask_question(request, pk):
    video = get_object_or_404(Video.objects.visible_to(request.user), pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.video = video
        comment.author = request.user
        comment.save()
        VideoQuestion.objects.create(comment=comment)
        notify_comment(comment)
    return redirect("video_detail", pk=video.pk)


@login_required
@require_POST
def feature_question_answer(request, reply_pk):
    reply = get_object_or_404(
        Comment.objects.select_related("video", "parent"),
        pk=reply_pk,
        parent__isnull=False,
        is_hidden=False,
    )
    if reply.video.author_id != request.user.pk:
        raise Http404("Reply not found")
    question = get_object_or_404(VideoQuestion, comment=reply.parent)
    question.featured_reply = None if question.featured_reply_id == reply.pk else reply
    question.save(update_fields=["featured_reply"])
    return redirect("video_detail", pk=reply.video_id)
