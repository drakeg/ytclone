from django.urls import path

from . import views

app_name = "monetization"

urlpatterns = [
    path("channel/<int:pk>/", views.creator_dashboard, name="creator_dashboard"),
    path("channel/<int:pk>/enable-sandbox/", views.enable_sandbox, name="enable_sandbox"),
    path("channel/<int:pk>/tiers/create/", views.tier_create, name="tier_create"),
    path("tiers/<int:tier_pk>/edit/", views.tier_edit, name="tier_edit"),
    path("tiers/<int:tier_pk>/toggle/", views.tier_toggle, name="tier_toggle"),
    path("channel/<int:pk>/tip/", views.tip_form, name="tip_form"),
    path("channel/<int:pk>/tip/send-sandbox/", views.send_sandbox_tip, name="send_sandbox_tip"),
    path("tiers/<int:tier_pk>/join-sandbox/", views.join_sandbox_membership, name="join_sandbox_membership"),
    path("memberships/<int:subscription_pk>/cancel-sandbox/", views.cancel_sandbox_membership, name="cancel_sandbox_membership"),
]
