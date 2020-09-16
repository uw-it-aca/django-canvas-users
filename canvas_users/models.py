from django.db import models
from django.utils.timezone import utc, localtime
from restclients_core.exceptions import DataFailureException
from canvas_users.dao.canvas import get_course_users
from canvas_users.dao.sis_provisioner import get_users_for_logins
import re


class AddUserManager(models.Manager):
    def users_in_course(self, course_id, section_id, role, logins):
        self._section_id = str(section_id)
        self._role = role

        self._course_users = dict(
            (u.sis_user_id, u) for u in get_course_users(course_id))

        return self._get_users_from_logins(logins)

    def _get_users_from_logins(self, logins):
        users = []
        for user_data in get_users_for_logins(logins):
            user = AddUser(login=user_data.login)
            if user_data.error is not None:
                user.status = 'invalid'
                user.comment = self._format_invalid_user(user_data.error)

            else:
                user.email = user_data.email
                user.regid = user_data.sis_id

                if user.regid in self._course_users:
                    existing_role = self._get_existing_role(user)
                    if existing_role:
                        # User already has a different role in the course
                        user.status = 'present'
                        user.comment = 'Already enrolled as {role}'.format(
                            role=self._format_role(existing_role))

                    elif self._user_in_section(user):
                        # User already in selected section with selected role
                        user.status = 'present'
                        user.comment = 'Already in this section'

                else:
                    user.name = user_data.full_name
            users.append(user)
        return users

    def _user_in_section(self, user):
        if user.regid in self._course_users:
            for enrollment in self._course_users[user.regid].enrollments:
                if str(enrollment.section_id) == self._section_id:
                    return True
        return False

    def _get_existing_role(self, user):
        if user.regid in self._course_users:
            for enrollment in self._course_users[user.regid].enrollments:
                if enrollment.role != self._role:
                    return enrollment.role

    def _format_invalid_user(self, err_str):
        match = re.match(r'^Invalid Gmail (username|domain): ', err_str)
        return 'Not a UW Netid or Gmail address' if match else err_str

    def _format_role(self, role):
        return re.sub(r'Enrollment$', '', role)


class AddUser(models.Model):
    """ Represents a set user to get added to Canvas
    """

    USER_VALID = 'valid'
    USER_INVALID = 'invalid'
    USER_PRESENT = 'present'

    STATUS_CHOICES = (
        (USER_VALID, 'valid'),
        (USER_INVALID, 'invalid'),
        (USER_PRESENT, 'present')
    )

    login = models.CharField(max_length=256)
    name = models.CharField(max_length=256, default='')
    regid = models.CharField(max_length=128, default='')
    email = models.CharField(max_length=128, default='')
    status = models.SlugField(
        max_length=8, choices=STATUS_CHOICES, default=USER_VALID)
    comment = models.CharField(max_length=80, default='Prepared to add')

    objects = AddUserManager()

    def json_data(self):
        return {
            'login': self.login,
            'name': self.name,
            'regid': self.regid,
            'status': self.status,
            'comment': self.comment
        }


class AddUsersImport(models.Model):
    import_pid = models.SmallIntegerField(null=True)
    importer = models.CharField(max_length=80)
    importer_id = models.CharField(max_length=16)
    importing = models.SmallIntegerField()
    imported = models.SmallIntegerField(default=0)
    course_id = models.CharField(max_length=80)
    section_id = models.CharField(max_length=80)
    role = models.CharField(max_length=80)
    start_date = models.DateTimeField(auto_now_add=True)
    finish_date = models.DateTimeField(null=True)
    import_error = models.TextField(null=True)

    def progress(self):
        if self.imported == self.importing:
            return 100

        return int((float(self.imported) / float(self.importing)) * 100)

    def json_data(self):
        return {
            'import_id': self.pk,
            'importing': self.importing,
            'imported': self.imported,
            'progress': self.progress(),
            'course_id': self.course_id,
            'section_id': self.section_id,
            'role': self.role,
            'start_date': localtime(self.start_date).isoformat(),
            'finish_date': localtime(
                self.finish_date).isoformat() if self.finish_date else None,
            'import_error': self.import_error
        }
