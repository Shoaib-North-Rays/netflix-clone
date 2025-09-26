from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import os

User = get_user_model()


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='genres/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Actor(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='actors/', null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Director(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='directors/', null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    QUALITY_CHOICES = [
        ('360p', '360p'),
        ('480p', '480p'), 
        ('720p', '720p HD'),
        ('1080p', '1080p Full HD'),
        ('4k', '4K Ultra HD'),
    ]
    
    RATING_CHOICES = [
        ('G', 'General Audiences'),
        ('PG', 'Parental Guidance'),
        ('PG-13', 'PG-13'),
        ('R', 'Restricted'),
        ('NC-17', 'Adults Only'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    release_year = models.IntegerField()
    duration = models.IntegerField(help_text="Duration in minutes")
    rating = models.CharField(max_length=10, choices=RATING_CHOICES, default='PG')
    imdb_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        null=True, blank=True
    )
    
    # Media files
    thumbnail = models.ImageField(upload_to='movies/thumbnails/')
    banner_image = models.ImageField(upload_to='movies/banners/', null=True, blank=True)
    trailer_url = models.URLField(blank=True, help_text="YouTube or external trailer URL")
    trailer_file = models.FileField(upload_to='movies/trailers/', null=True, blank=True)
    
    # Relationships
    genres = models.ManyToManyField(Genre, related_name='movies')
    actors = models.ManyToManyField(Actor, related_name='movies')
    directors = models.ManyToManyField(Director, related_name='movies')
    
    # Metadata
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_new_release = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.release_year})"
    
    class Meta:
        ordering = ['-created_at']
        
    @property
    def duration_formatted(self):
        hours = self.duration // 60
        minutes = self.duration % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


class VideoFile(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='video_files')
    quality = models.CharField(max_length=10, choices=Movie.QUALITY_CHOICES)
    file_path = models.FileField(upload_to='movies/videos/')
    file_size = models.BigIntegerField(help_text="File size in bytes")
    duration = models.IntegerField(help_text="Duration in seconds")
    
    # HLS specific fields
    hls_playlist = models.FileField(upload_to='movies/hls/', null=True, blank=True, help_text=".m3u8 playlist file")
    hls_segments_path = models.CharField(max_length=500, blank=True, help_text="Path to HLS segments directory")
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.movie.title} - {self.quality}"
    
    class Meta:
        unique_together = ['movie', 'quality']
        ordering = ['quality']


class MovieRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='user_ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'movie']
    
    def __str__(self):
        return f"{self.user.email} rated {self.movie.title}: {self.rating}/5"


class MovieLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'movie']
    
    def __str__(self):
        return f"{self.user.email} liked {self.movie.title}"


class TVShow(models.Model):
    RATING_CHOICES = [
        ('G', 'General Audiences'),
        ('PG', 'Parental Guidance'),
        ('PG-13', 'PG-13'),
        ('R', 'Restricted'),
        ('TV-MA', 'TV Mature Audiences'),
        ('TV-14', 'TV-14'),
        ('TV-PG', 'TV Parental Guidance'),
        ('TV-G', 'TV General Audiences'),
    ]
    
    STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
        ('hiatus', 'On Hiatus'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    first_air_date = models.DateField()
    last_air_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    rating = models.CharField(max_length=10, choices=RATING_CHOICES, default='TV-PG')
    imdb_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        null=True, blank=True
    )
    
    # Media files
    thumbnail = models.ImageField(upload_to='tvshows/thumbnails/', null=True, blank=True)
    banner_image = models.ImageField(upload_to='tvshows/banners/', null=True, blank=True)
    trailer_url = models.URLField(blank=True, help_text="YouTube or external trailer URL")
    
    # Relationships
    genres = models.ManyToManyField(Genre, related_name='tvshows')
    actors = models.ManyToManyField(Actor, related_name='tvshows')
    directors = models.ManyToManyField(Director, related_name='tvshows')
    
    # Metadata
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_new_release = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.first_air_date.year})"
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def total_seasons(self):
        return self.seasons.count()
    
    @property
    def total_episodes(self):
        return sum(season.episodes.count() for season in self.seasons.all())
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


class Season(models.Model):
    tvshow = models.ForeignKey(TVShow, on_delete=models.CASCADE, related_name='seasons')
    season_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    air_date = models.DateField(null=True, blank=True)
    poster = models.ImageField(upload_to='tvshows/seasons/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['tvshow', 'season_number']
        ordering = ['season_number']
    
    def __str__(self):
        return f"{self.tvshow.title} - Season {self.season_number}"
    
    @property
    def episode_count(self):
        return self.episodes.count()


class Episode(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='episodes')
    episode_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    air_date = models.DateField(null=True, blank=True)
    duration = models.IntegerField(help_text="Duration in minutes")
    
    # Media files
    thumbnail = models.ImageField(upload_to='tvshows/episodes/', null=True, blank=True)
    video_file = models.FileField(upload_to='tvshows/videos/', null=True, blank=True)
    
    # HLS specific fields
    hls_playlist = models.FileField(upload_to='tvshows/hls/', null=True, blank=True, help_text=".m3u8 playlist file")
    
    # Metadata
    view_count = models.PositiveIntegerField(default=0)
    is_processed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['season', 'episode_number']
        ordering = ['episode_number']
    
    def __str__(self):
        return f"{self.season.tvshow.title} S{self.season.season_number}E{self.episode_number} - {self.title}"
    
    @property
    def duration_formatted(self):
        hours = self.duration // 60
        minutes = self.duration % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


class TVShowRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tvshow = models.ForeignKey(TVShow, on_delete=models.CASCADE, related_name='user_ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'tvshow']
    
    def __str__(self):
        return f"{self.user.email} rated {self.tvshow.title}: {self.rating}/5"


class TVShowLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tvshow = models.ForeignKey(TVShow, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'tvshow']
    
    def __str__(self):
        return f"{self.user.email} liked {self.tvshow.title}"


class EpisodeWatchHistory(models.Model):
    user_profile = models.ForeignKey('users.UserProfile', on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)
    watch_duration = models.IntegerField(default=0)  # in seconds
    completed = models.BooleanField(default=False)
    last_position = models.IntegerField(default=0)  # last watched position in seconds
    
    class Meta:
        unique_together = ['user_profile', 'episode']
        ordering = ['-watched_at']
    
    def __str__(self):
        return f"{self.user_profile.user.email} - {self.episode.title}"
