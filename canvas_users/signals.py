from django.dispatch import receiver
from django.db.models.signals import post_save
from canvas_users.models import AddUsersImport


@receiver(post_save, sender=AddUsersImport)
def user_import(sender, instance, created, raw, using, update_fields):
    if update_fields is not None and 'import_pid' in update_fields:
        instance.import_users()
