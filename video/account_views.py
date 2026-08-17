from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .channel_forms import ChannelForm


@login_required
def current_profile(request):
    return redirect("user_profile", username=request.user.username)


@login_required
def channel_create(request):
    if request.method == "POST":
        form = ChannelForm(request.POST, request.FILES)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.owner = request.user
            channel.save()
            return redirect("channel_detail", pk=channel.pk)
    else:
        form = ChannelForm()

    return render(request, "videos/channel_form.html", {"form": form})
