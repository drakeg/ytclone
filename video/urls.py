from django.urls import path
from . import views

urlpatterns = [
    path('', views.video_list, name='video_list'),
    path('videos/<int:pk>/', views.video_detail, name='video_detail'),
    path('videos/<int:pk>/like/', views.like_video, name='like_video'),
    path('videos/<int:pk>/dislike/', views.dislike_video, name='dislike_video'),
    path('channels/', views.channel_list, name='channel_list'),
    path('channels/<int:pk>/', views.channel_detail, name='channel_detail'),
    path('channels/<int:pk>/subscribe/', views.subscribe, name='subscribe'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('search/', views.search, name='search'),
    path('filter/', views.filter_videos, name='filter'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('profile/<str:username>/edit/', views.edit_profile, name='edit_profile'),
    path('upload/', views.upload_video, name='upload'),
]
