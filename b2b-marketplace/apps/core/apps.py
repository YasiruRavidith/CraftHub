from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core' # If 'core' is a top-level app
    # If 'core' is inside 'apps/' directory, then use:
    # name = 'apps.core'