from django.apps import AppConfig

class ReviewsRatingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reviews_ratings'

    def ready(self):
        import apps.reviews_ratings.signals # For updating average ratings, etc.