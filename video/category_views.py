from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from .category_forms import CategoryForm
from .services.channels import accessible_channels


@login_required
def category_create(request):
    if not accessible_channels(request.user).exists():
        return HttpResponseForbidden("Create a channel before creating categories.")

    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            return redirect("category_detail", pk=category.pk)
    else:
        form = CategoryForm()

    return render(request, "videos/category_form.html", {"form": form})
