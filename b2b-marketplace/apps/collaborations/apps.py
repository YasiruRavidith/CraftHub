from django.apps import AppConfig

class CollaborationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.collaborations'

    def ready(self):
        # import apps.collaborations.signals # If you have signals
        pass