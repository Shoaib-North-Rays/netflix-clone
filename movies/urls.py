from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views

# API Router
router = DefaultRouter()
router.register(r'movies', api_views.MovieViewSet)
router.register(r'genres', api_views.GenreViewSet)
router.register(r'actors', api_views.ActorViewSet)

urlpatterns = [
    # API URLs
    path('', include(router.urls)),
    
    # Custom API endpoints
    path('movies/<int:movie_id>/toggle-like/', api_views.toggle_movie_like, name='toggle_movie_like'),
    path('movies/<int:movie_id>/rate/', api_views.rate_movie, name='rate_movie'),
    path('search/', api_views.search_movies, name='search_movies'),
]
