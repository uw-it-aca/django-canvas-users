from django.core.management.base import BaseCommand
from canvas_users.models import AddUsersImport


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            imp = AddUsersImport.objects.find_import()
            try:
                imp.import_users()
            except Exception:
                pass
        except AddUsersImport.DoesNotExist:
            pass
