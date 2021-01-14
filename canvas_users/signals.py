from django.dispatch import receiver
from django.db.models.signals import post_save
from canvas_users.models import AddUsersImport


@receiver(post_save, sender=AddUsersImport)
def user_import(sender, instance, **kwargs):
    if kwargs['update_fields'] and 'import_pid' in kwargs['update_fields']:
        instance.import_users()
