from django.core.management.base import BaseCommand
from restclients_core.exceptions import DataFailureException
from canvas_users.models import AddUsersImport


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            imp = AddUsersImport.objects.find_import()
            imp.import_users()
        except AddUsersImport.DoesNotExist:
            pass
        except DataFailureException:
            pass
