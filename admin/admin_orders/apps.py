from django.apps import AppConfig


class AdminOrderConfig(AppConfig):

    default_auto_field = 'django.db.models.BigAutoField'

    name = 'admin.admin_orders'


    def ready(self):

        import admin.admin_orders.signals