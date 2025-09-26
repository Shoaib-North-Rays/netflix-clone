from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('movies/', views.movies, name='movies'),
    path('tv-shows/', views.tvshows, name='tvshows'),
    path('pricing/', views.pricing, name='pricing'),
    path('my-list/', views.my_list, name='my_list'),
    
    # Movie pages
    path('movie/<slug:slug>/', views.movie_detail, name='movie_detail'),
    path('watch/<slug:slug>/', views.watch_movie, name='watch_movie'),
    
    # TV Show pages
    path('tv-show/<slug:slug>/', views.tvshow_detail, name='tvshow_detail'),
    path('watch/<slug:show_slug>/s<int:season_number>/e<int:episode_number>/', views.watch_episode, name='watch_episode'),
    
    # AJAX endpoints
    path('api/toggle-watchlist/<int:movie_id>/', views.toggle_watchlist, name='toggle_watchlist'),
    path('api/toggle-tvshow-watchlist/<int:tvshow_id>/', views.toggle_tvshow_watchlist, name='toggle_tvshow_watchlist'),
]
