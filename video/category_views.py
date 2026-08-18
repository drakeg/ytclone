from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .category_forms import CategoryForm
from .models import Category
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


@login_required
@require_POST
def category_create_inline(request):
    if not accessible_channels(request.user).exists():
        return JsonResponse({"error": "Create a channel before creating categories."}, status=403)

    name = request.POST.get("name", "").strip()
    if not name:
        return JsonResponse({"error": "Enter a category name."}, status=400)
    if len(name) > 255:
        return JsonResponse({"error": "Category names must be 255 characters or fewer."}, status=400)

    category = Category.objects.filter(name__iexact=name).first()
    created = category is None
    if category is None:
        category = Category.objects.create(name=name)

    return JsonResponse(
        {"id": category.pk, "name": category.name, "created": created},
        status=201 if created else 200,
    )
