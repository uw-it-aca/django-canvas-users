from django.apps import AppConfig


class CanvasUsersConfig(AppConfig):
    name = 'canvas_users'

    def ready(self):
        import canvas_users.signals
