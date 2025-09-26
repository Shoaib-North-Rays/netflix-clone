from rest_framework import serializers
from .models import Movie, Genre, Actor, Director, VideoFile, MovieRating, MovieLike


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug', 'description']


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ['id', 'name', 'bio', 'nationality', 'photo']


class DirectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director
        fields = ['id', 'name', 'bio', 'nationality', 'photo']


class VideoFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoFile
        fields = ['id', 'quality', 'file_size', 'duration', 'is_processed']


class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    duration_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'slug', 'description', 'release_year', 'duration', 
            'duration_formatted', 'rating', 'imdb_rating', 'thumbnail', 
            'banner_image', 'genres', 'view_count', 'like_count', 'is_featured',
            'is_trending', 'is_new_release', 'created_at'
        ]


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)
    directors = DirectorSerializer(many=True, read_only=True)
    video_files = VideoFileSerializer(many=True, read_only=True)
    duration_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'slug', 'description', 'release_year', 'duration',
            'duration_formatted', 'rating', 'imdb_rating', 'thumbnail', 
            'banner_image', 'trailer_url', 'trailer_file', 'genres', 'actors', 
            'directors', 'video_files', 'view_count', 'like_count', 'is_featured',
            'is_trending', 'is_new_release', 'created_at', 'updated_at'
        ]


class MovieRatingSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = MovieRating
        fields = ['id', 'rating', 'review', 'user_email', 'created_at', 'updated_at']