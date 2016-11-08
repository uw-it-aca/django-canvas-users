from django.db import models
from django.utils.timezone import utc, localtime
from restclients.canvas.users import Users
from restclients.models.sws import Person
from restclients.exceptions import DataFailureException
from sis_provisioner.dao.user import get_person_by_netid, user_email,\
    user_fullname, user_sis_id, get_person_by_gmail_id
from sis_provisioner.exceptions import UserPolicyException
import re


class AddUserManager(models.Manager):
    def users_in_course(self, course_id, logins, as_user=None):
        uw_domains = ['uw.edu', 'washington.edu',
                      'u.washington.edu', 'cac.washington.edu',
                      'deskmail.washington.edu']
        self._re_uw_domain = re.compile(r'^(.*)@(%s)$' % '|'.join(uw_domains))

        course_users = Users().get_users_for_course(course_id,
                                                    params={'per_page': 1000})
        self._course_users = dict((u.sis_user_id, u) for u in course_users)

        return map(self._get_user_from_login, self._normalize_list(logins))

    def _normalize_list(self, raw_logins):
        logins = []
        for raw in raw_logins:
            login = self._normalize(raw)
            if login not in logins:
                logins.append(login)

        return logins

    def _get_user_from_login(self, login):
        user = AddUser(login=login)
        try:
            try:
                person = get_person_by_gmail_id(login)
                user.login = canvas_user.login_id
            except UserPolicyException:
                person = get_person_by_netid(login)
                user.login = person.uwnetid

            user.email = user_email(person)
            user.name = user_fullname(person)
            user.regid = user_sis_id(person)

            if user.regid in self._course_users:
                user.name = self._course_users[user.regid].name
                user.status = 'present'
                user.comment = 'Already in course'

        except DataFailureException as ex:
            if ex.status != 401:
                raise
        except UserPolicyException as ex:
            user.status = 'invalid'
            user.comment = "%s" % self._prettify(str(ex))

        return user

    def _normalize(self, login):
        match = self._re_uw_domain.match(login)
        return match.group(1) if match else login

    def _prettify(self, err_str):
        match = re.match(r'^Invalid Gmail (username|domain): ', err_str)
        return 'Not a UW Netid or Gmail address' if match else err_str


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
