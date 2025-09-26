from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from movies.models import Genre, Actor, Director, Movie
from users.models import SubscriptionPlan, UserProfile
from django.utils.text import slugify

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for the Netflix clone'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create subscription plans
        self.create_subscription_plans()
        
        # Create genres
        genres = self.create_genres()
        
        # Create actors and directors
        actors = self.create_actors()
        directors = self.create_directors()
        
        # Create movies
        self.create_movies(genres, actors, directors)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )

    def create_subscription_plans(self):
        """Create subscription plans"""
        plans_data = [
            {
                'name': 'free',
                'display_name': 'Free',
                'price': 0.00,
                'duration_days': 30,
                'max_streams': 1,
                'hd_quality': False,
                'ultra_hd_quality': False,
                'download_allowed': False,
                'description': 'Limited content with ads'
            },
            {
                'name': 'basic',
                'display_name': 'Basic',
                'price': 8.99,
                'duration_days': 30,
                'max_streams': 1,
                'hd_quality': False,
                'ultra_hd_quality': False,
                'download_allowed': False,
                'description': 'Watch on 1 device at a time'
            },
            {
                'name': 'standard',
                'display_name': 'Standard',
                'price': 13.99,
                'duration_days': 30,
                'max_streams': 2,
                'hd_quality': True,
                'ultra_hd_quality': False,
                'download_allowed': True,
                'description': 'Watch on 2 devices, HD quality'
            },
            {
                'name': 'premium',
                'display_name': 'Premium',
                'price': 17.99,
                'duration_days': 30,
                'max_streams': 4,
                'hd_quality': True,
                'ultra_hd_quality': True,
                'download_allowed': True,
                'description': 'Watch on 4 devices, Ultra HD quality'
            }
        ]
        
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'Created subscription plan: {plan.display_name}')

    def create_genres(self):
        """Create movie genres"""
        genres_data = [
            {'name': 'Action', 'description': 'High-octane movies with thrilling sequences'},
            {'name': 'Comedy', 'description': 'Light-hearted and funny movies'},
            {'name': 'Drama', 'description': 'Serious and emotional storylines'},
            {'name': 'Horror', 'description': 'Scary and suspenseful movies'},
            {'name': 'Romance', 'description': 'Love stories and romantic themes'},
            {'name': 'Sci-Fi', 'description': 'Science fiction and futuristic themes'},
            {'name': 'Thriller', 'description': 'Suspenseful and tension-filled movies'},
            {'name': 'Adventure', 'description': 'Exciting journeys and quests'},
            {'name': 'Animation', 'description': 'Animated movies for all ages'},
            {'name': 'Documentary', 'description': 'Non-fiction and educational content'}
        ]
        
        genres = []
        for genre_data in genres_data:
            genre, created = Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults={
                    'slug': slugify(genre_data['name']),
                    'description': genre_data['description']
                }
            )
            genres.append(genre)
            if created:
                self.stdout.write(f'Created genre: {genre.name}')
        
        return genres

    def create_actors(self):
        """Create sample actors"""
        actors_data = [
            {'name': 'John Smith', 'nationality': 'American'},
            {'name': 'Emma Watson', 'nationality': 'British'},
            {'name': 'Ryan Gosling', 'nationality': 'Canadian'},
            {'name': 'Scarlett Johansson', 'nationality': 'American'},
            {'name': 'Tom Hardy', 'nationality': 'British'},
            {'name': 'Jennifer Lawrence', 'nationality': 'American'},
            {'name': 'Leonardo DiCaprio', 'nationality': 'American'},
            {'name': 'Margot Robbie', 'nationality': 'Australian'},
            {'name': 'Chris Evans', 'nationality': 'American'},
            {'name': 'Natalie Portman', 'nationality': 'Israeli-American'}
        ]
        
        actors = []
        for actor_data in actors_data:
            actor, created = Actor.objects.get_or_create(
                name=actor_data['name'],
                defaults={'nationality': actor_data['nationality']}
            )
            actors.append(actor)
            if created:
                self.stdout.write(f'Created actor: {actor.name}')
        
        return actors

    def create_directors(self):
        """Create sample directors"""
        directors_data = [
            {'name': 'Christopher Nolan', 'nationality': 'British'},
            {'name': 'Quentin Tarantino', 'nationality': 'American'},
            {'name': 'Martin Scorsese', 'nationality': 'American'},
            {'name': 'Steven Spielberg', 'nationality': 'American'},
            {'name': 'Denis Villeneuve', 'nationality': 'Canadian'},
            {'name': 'Greta Gerwig', 'nationality': 'American'},
            {'name': 'Jordan Peele', 'nationality': 'American'},
            {'name': 'Rian Johnson', 'nationality': 'American'}
        ]
        
        directors = []
        for director_data in directors_data:
            director, created = Director.objects.get_or_create(
                name=director_data['name'],
                defaults={'nationality': director_data['nationality']}
            )
            directors.append(director)
            if created:
                self.stdout.write(f'Created director: {director.name}')
        
        return directors

    def create_movies(self, genres, actors, directors):
        """Create sample movies"""
        movies_data = [
            {
                'title': 'The Dark Knight',
                'description': 'Batman faces his greatest challenge yet when the Joker wreaks havoc on Gotham City.',
                'release_year': 2008,
                'duration': 152,
                'rating': 'PG-13',
                'imdb_rating': 9.0,
                'is_featured': True,
                'is_trending': True,
                'genres': ['Action', 'Crime', 'Drama'],
                'actors': ['John Smith', 'Tom Hardy'],
                'directors': ['Christopher Nolan']
            },
            {
                'title': 'Inception',
                'description': 'A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea.',
                'release_year': 2010,
                'duration': 148,
                'rating': 'PG-13',
                'imdb_rating': 8.8,
                'is_featured': True,
                'genres': ['Action', 'Sci-Fi', 'Thriller'],
                'actors': ['Leonardo DiCaprio', 'Scarlett Johansson'],
                'directors': ['Christopher Nolan']
            },
            {
                'title': 'La La Land',
                'description': 'A jazz musician and an aspiring actress meet and fall in love in Los Angeles.',
                'release_year': 2016,
                'duration': 128,
                'rating': 'PG-13',
                'imdb_rating': 8.0,
                'is_new_release': True,
                'genres': ['Romance', 'Drama'],
                'actors': ['Ryan Gosling', 'Emma Watson'],
                'directors': ['Greta Gerwig']
            },
            {
                'title': 'Avengers: Endgame',
                'description': 'The Avengers assemble once more to reverse the damage caused by Thanos.',
                'release_year': 2019,
                'duration': 181,
                'rating': 'PG-13',
                'imdb_rating': 8.4,
                'is_trending': True,
                'genres': ['Action', 'Adventure', 'Sci-Fi'],
                'actors': ['Chris Evans', 'Scarlett Johansson'],
                'directors': ['Christopher Nolan']
            },
            {
                'title': 'Pulp Fiction',
                'description': 'The lives of two mob hitmen, a boxer, and others intertwine in this crime saga.',
                'release_year': 1994,
                'duration': 154,
                'rating': 'R',
                'imdb_rating': 8.9,
                'genres': ['Crime', 'Drama'],
                'actors': ['John Smith', 'Natalie Portman'],
                'directors': ['Quentin Tarantino']
            },
            {
                'title': 'The Shape of Water',
                'description': 'A mute woman discovers a classified experiment and falls in love with an amphibious creature.',
                'release_year': 2017,
                'duration': 123,
                'rating': 'R',
                'imdb_rating': 7.3,
                'genres': ['Romance', 'Thriller'],
                'actors': ['Jennifer Lawrence', 'Tom Hardy'],
                'directors': ['Denis Villeneuve']
            }
        ]
        
        for movie_data in movies_data:
            movie, created = Movie.objects.get_or_create(
                title=movie_data['title'],
                defaults={
                    'slug': slugify(movie_data['title']),
                    'description': movie_data['description'],
                    'release_year': movie_data['release_year'],
                    'duration': movie_data['duration'],
                    'rating': movie_data['rating'],
                    'imdb_rating': movie_data['imdb_rating'],
                    'is_featured': movie_data.get('is_featured', False),
                    'is_trending': movie_data.get('is_trending', False),
                    'is_new_release': movie_data.get('is_new_release', False),
                }
            )
            
            if created:
                # Add genres
                movie_genres = Genre.objects.filter(name__in=movie_data['genres'])
                movie.genres.set(movie_genres)
                
                # Add actors
                movie_actors = Actor.objects.filter(name__in=movie_data['actors'])
                movie.actors.set(movie_actors)
                
                # Add directors
                movie_directors = Director.objects.filter(name__in=movie_data['directors'])
                movie.directors.set(movie_directors)
                
                self.stdout.write(f'Created movie: {movie.title}')