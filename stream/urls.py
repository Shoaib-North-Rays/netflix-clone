from django.urls import path
from . import views

urlpatterns = [
    path('get-stream-url/<str:movie_slug>/', views.get_video_stream_url, name='get_stream_url'),
    path('video/<str:video_token>/', views.stream_video, name='stream_video'),
]
