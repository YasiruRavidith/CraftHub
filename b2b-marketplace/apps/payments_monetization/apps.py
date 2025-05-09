from django.apps import AppConfig

class PaymentsMonetizationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments_monetization'

    def ready(self):
        import apps.payments_monetization.signals # For handling subscription events, etc.