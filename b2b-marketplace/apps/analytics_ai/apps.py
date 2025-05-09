from django.apps import AppConfig

class AnalyticsAiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics_ai'

    def ready(self):
        # import apps.analytics_ai.signals # If you have signals
        pass