from django.urls import path

from . import views

app_name = "monetization"

urlpatterns = [
    path("channel/<int:pk>/", views.creator_dashboard, name="creator_dashboard"),
    path("channel/<int:pk>/enable-sandbox/", views.enable_sandbox, name="enable_sandbox"),
    path("channel/<int:pk>/tiers/create/", views.tier_create, name="tier_create"),
    path("channel/<int:pk>/tip/", views.tip_form, name="tip_form"),
    path("channel/<int:pk>/tip/send-sandbox/", views.send_sandbox_tip, name="send_sandbox_tip"),
    path("tiers/<int:tier_pk>/join-sandbox/", views.join_sandbox_membership, name="join_sandbox_membership"),
]
