from django.apps import AppConfig


class PayeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payees'

    def ready(self):
        import payees.signals
