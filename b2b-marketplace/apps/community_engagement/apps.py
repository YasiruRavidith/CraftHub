from django.apps import AppConfig

class CommunityEngagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.community_engagement'

    def ready(self):
        # import apps.community_engagement.signals # If you have signals for this app
        pass