from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Movie, Genre, Actor, MovieRating, MovieLike
from .serializers import (
    MovieSerializer, MovieDetailSerializer, GenreSerializer, 
    ActorSerializer, MovieRatingSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving movies
    """
    queryset = Movie.objects.filter(is_active=True).select_related().prefetch_related(
        'genres', 'actors', 'directors', 'video_files'
    )
    serializer_class = MovieSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['genres__slug', 'release_year', 'rating', 'is_featured', 'is_trending']
    search_fields = ['title', 'description', 'actors__name', 'directors__name']
    ordering_fields = ['created_at', 'release_year', 'imdb_rating', 'view_count', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailSerializer
        return MovieSerializer
    
    def get_permissions(self):
        """
        Allow anyone to view movies list/details
        """
        return [AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        """
        Increment view count when retrieving movie details
        """
        instance = self.get_object()
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing genres
    """
    queryset = Genre.objects.filter(is_active=True)
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


class ActorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing actors
    """
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'nationality']


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_movie_like(request, movie_id):
    """
    Toggle like/unlike for a movie
    """
    movie = get_object_or_404(Movie, id=movie_id, is_active=True)
    
    like, created = MovieLike.objects.get_or_create(
        user=request.user,
        movie=movie
    )
    
    if not created:
        # Unlike - remove the like
        like.delete()
        liked = False
    else:
        # Like - like was created
        liked = True
    
    # Update movie like count
    movie.like_count = movie.likes.count()
    movie.save(update_fields=['like_count'])
    
    return Response({
        'success': True,
        'liked': liked,
        'like_count': movie.like_count
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_movie(request, movie_id):
    """
    Rate a movie (1-5 stars)
    """
    movie = get_object_or_404(Movie, id=movie_id, is_active=True)
    rating_value = request.data.get('rating')
    review_text = request.data.get('review', '')
    
    if not rating_value or not (1 <= int(rating_value) <= 5):
        return Response({
            'error': 'Rating must be between 1 and 5'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create or update rating
    rating, created = MovieRating.objects.update_or_create(
        user=request.user,
        movie=movie,
        defaults={
            'rating': rating_value,
            'review': review_text
        }
    )
    
    serializer = MovieRatingSerializer(rating)
    return Response({
        'success': True,
        'created': created,
        'rating': serializer.data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def search_movies(request):
    """
    Advanced movie search
    """
    query = request.GET.get('q', '')
    genre = request.GET.get('genre', '')
    year = request.GET.get('year', '')
    rating = request.GET.get('rating', '')
    
    movies = Movie.objects.filter(is_active=True)
    
    if query:
        movies = movies.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(actors__name__icontains=query) |
            Q(directors__name__icontains=query)
        ).distinct()
    
    if genre:
        movies = movies.filter(genres__slug=genre)
    
    if year:
        movies = movies.filter(release_year=year)
    
    if rating:
        movies = movies.filter(rating=rating)
    
    # Paginate results
    paginator = StandardResultsSetPagination()
    result_page = paginator.paginate_queryset(movies, request)
    
    serializer = MovieSerializer(result_page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)