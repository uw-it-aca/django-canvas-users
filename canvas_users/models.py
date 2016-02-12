from django.db import models
from django.utils.timezone import utc, localtime
from restclients.canvas.users import Users
from restclients.models.sws import Person
from restclients.exceptions import DataFailureException
from sis_provisioner.policy import UserPolicy, UserPolicyException
import re


class AddUserManager(models.Manager):
    def users_in_course(self, course_id, logins, as_user=None):
        self._course_id = course_id
        uw_domains = ['uw.edu', 'washington.edu',
                      'u.washington.edu', 'cac.washington.edu',
                      'deskmail.washington.edu']
        self._re_uw_domain = re.compile(r'^(.*)@(%s)$' % '|'.join(uw_domains))
        self._user_policy = UserPolicy()
        self._users_api = Users(as_user=as_user)

        return map(self._get_user_from_login, self._normalize_list(logins))

    def _normalize_list(self, raw_logins):
        logins = []
        for raw in raw_logins:
            login = self._normalize(raw)
            if login not in logins:
                logins.append(login)

        return logins

    def _get_user_from_login(self, login):
        try:
            user = AddUser(login=login)
            self._user_policy.valid(user.login)
            if '@' in login:
                try:
                    canvas_user = self._user_policy.get_person_by_gmail_id(user.login)
                    user.regid = canvas_user.sis_user_id
                except UserPolicyException:
                    raise UserPolicyException('Invalid user ID')
            elif len(user.login) < 3:
                raise UserPolicyException('Invalid NetID')
            else:
                person = self._user_policy.get_person_by_netid(user.login)
                user.name = person.full_name if (
                    isinstance(person, Person)) else person.display_name

                user.regid = person.uwregid

            for e in self._users_api.get_users_for_course(
                    self._course_id, params={"search_term": login}):
                if e.login_id == login:
                    user.name = e.name
                    user.status = 'present'
                    user.comment = 'Already in course'
                    break

        except DataFailureException as ex:
            if ex.status != 401:
                raise
        except UserPolicyException as ex:
            user.status = 'invalid'
            user.comment = "%s" % ex

        return user

    def _normalize(self, login):
        match = self._re_uw_domain.match(login)
        return match.group(1) if match else login


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
    name = models.CharField(max_length=256,default='')
    regid = models.CharField(max_length=128,default='')
    status= models.SlugField(max_length=8, choices=STATUS_CHOICES,default=USER_VALID)
    comment = models.CharField(max_length=80,default='Prepared to add')

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

        return int((float(self.imported)/float(self.importing))*100)

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
            'finish_date': localtime(self.finish_date).isoformat() if self.finish_date else None,
            'import_error': self.import_error
        }
