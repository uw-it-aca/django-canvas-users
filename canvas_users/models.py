from django.db import models
from django.utils.timezone import utc, localtime
from restclients_core.exceptions import DataFailureException
from canvas_users.dao.canvas import (
    get_course_users, get_user_by_sis_id, create_user, enroll_course_user)
from canvas_users.dao.sis_provisioner import validate_logins
from logging import getLogger
from os import getpid
import re

logger = getLogger(__name__)


class AddUsersImportManager(models.Manager):
    def find_import(self):
        imp = AddUsersImport.objects.filter(
            import_pid__isnull=True, finish_date__isnull=True).earliest(
                'start_date')
        imp.import_pid = getpid()
        imp.save()
        return imp


class AddUsersImport(models.Model):
    import_pid = models.SmallIntegerField(null=True)
    importer = models.CharField(max_length=80)
    importer_id = models.CharField(max_length=16)
    importing = models.SmallIntegerField()
    imported = models.SmallIntegerField(default=0)
    course_id = models.CharField(max_length=80)
    section_id = models.CharField(max_length=80)
    section_only = models.NullBooleanField()
    notify_users = models.NullBooleanField()
    role = models.CharField(max_length=80)
    role_id = models.CharField(max_length=80)
    role_base = models.CharField(max_length=80)
    start_date = models.DateTimeField(auto_now_add=True)
    finish_date = models.DateTimeField(null=True)
    import_error = models.TextField(null=True)

    objects = AddUsersImportManager()

    def start(self):
        self.import_pid = getpid()
        self.save(update_fields=['import_pid'])

    def import_users(self):
        for user in self.adduser_set.filter(status=AddUser.USER_VALID):
            self._import_user(user)
            self.imported += 1
            self.save(update_fields=['imported'])

        self.finish_date = datetime.now()
        self.save(update_fields=['finish_date'])

    def _import_user(self, user):
        try:
            canvas_user = get_user_by_sis_id(user.regid)
        except DataFailureException as ex:
            if ex.status == 404:
                logger.info(
                    'CREATE USER "{}", login: {}, reg_id: {}'.format(
                        user.name, user.login, user.regid))

                # Add user as "admin" on behalf of importer
                canvas_user = create_user(name=user.name,
                                          login_id=user.login,
                                          sis_user_id=user.regid,
                                          email=user.email)
            else:
                self.import_error = 'ERROR creating user {}, {}: {}'.format(
                    user.login, user.regid, ex)
                self.save()
                logger.error(self.import_error)
                raise

        logger.info(
            '{importer} ADDING {user} ({user_id}) TO {course_id}: '
            '{sis_section_id} ({section_id}) AS {role} ({role_id}) '
            '- O:{section_only}, N:{notify}'.format(
                importer=self.importer, user=user.login,
                user_id=canvas_user.user_id,
                course_id=self.course_id,
                sis_section_id=self.section_id,
                section_id=section.section_id,
                role=self.role,
                role_id=role.role_id,
                section_only=self.section_only,
                notify=self.notify_users))

        try:
            enroll_course_user(
                as_user=imp.importer_id,
                course_id=self.course_id,
                section_id=self.section_id,
                user_id=canvas_user.user_id,
                role_type=self.role_base,
                role_id=self.role_id,
                section_only=self.section_only,
                notify_users=self.notify_users)

        except DataFailureException as ex:
            self.import_error = 'ERROR enrolling user {}, {}: {}'.format(
                user.login, self.section_id, ex)
            self.save()
            logger.error(self.import_error)
            raise

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


class AddUserManager(models.Manager):
    def users_in_course(self, course_id, section_id, role, logins):
        self._section_id = str(section_id)
        self._role = role

        self._course_users = dict(
            (u.sis_user_id, u) for u in get_course_users(course_id))

        return self._get_users_from_logins(logins)

    def _get_users_from_logins(self, logins):
        users = []
        for user_data in validate_logins(logins):
            user = AddUser(login=user_data.get('login'))
            if user_data.get('error') is not None:
                user.status = AddUser.USER_INVALID
                user.comment = self._format_invalid_user(user_data['error'])

            else:
                user.email = user_data.get('email')
                user.regid = user_data.get('sis_id')

                if user.regid in self._course_users:
                    existing_role = self._get_existing_role(user)
                    if existing_role:
                        # User already has a different role in the course
                        user.status = AddUser.USER_PRESENT
                        user.comment = 'Already enrolled as {role}'.format(
                            role=self._format_role(existing_role))

                    elif self._user_in_section(user):
                        # User already in selected section with selected role
                        user.status = AddUser.USER_PRESENT
                        user.comment = 'Already in this section'

                else:
                    user.name = user_data.get('full_name')

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
    importjob = models.ForeignKey(AddUsersImport, on_delete=models.CASCADE)

    objects = AddUserManager()

    def json_data(self):
        return {
            'login': self.login,
            'name': self.name,
            'regid': self.regid,
            'status': self.status,
            'comment': self.comment
        }
