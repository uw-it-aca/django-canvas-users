from django.test import TestCase
from canvas_users.models import AddUserManager, AddUser, AddUsersImport
from canvas_users.views import allow_origin


class AddUserManagerTest(TestCase):
    def test_users_in_course(self):
        pass

    def test_user_in_section(self):
        pass

    def test_get_existing_role(self):
        pass

    def test_normalize(self):
        with self.settings(
                ADD_USER_DOMAIN_WHITELIST=['abc.com', 'xyz.edu']):

            self.assertEquals(AddUserManager()._normalize(
                'joe@abc.com'), 'joe')
            self.assertEquals(AddUserManager()._normalize(
                'joe@xyz.edu'), 'joe')
            self.assertEquals(AddUserManager()._normalize(
                'joe@mail.com'), 'joe@mail.com')

    def test_format_invalid_user(self):
        self.assertEquals(AddUserManager()._format_invalid_user(
            'Invalid Gmail username: abc'), 'Not a UW Netid or Gmail address')
        self.assertEquals(AddUserManager()._format_invalid_user(
            'Invalid Gmail domain: abc'), 'Not a UW Netid or Gmail address')
        self.assertEquals(AddUserManager()._format_invalid_user(
            'Invalid user'), 'Invalid user')

    def test_format_role(self):
        self.assertEquals(AddUserManager()._format_role(
            'TeacherEnrollment'), 'Teacher')


class AddUsersImportTest(TestCase):
    def test_progress(self):
        self.assertEquals(AddUsersImport(
            imported=100, importing=100).progress(), 100)
        self.assertEquals(AddUsersImport(
            imported=35, importing=35).progress(), 100)
        self.assertEquals(AddUsersImport(
            imported=0, importing=50).progress(), 0)
        self.assertEquals(AddUsersImport(
            imported=2, importing=7).progress(), 28)
        self.assertEquals(AddUsersImport(
            imported=9, importing=12).progress(), 75)


class AllowOriginTest(TestCase):
    def test_allow_origin(self):
        origin = 'https://canvas.edu'
        with self.settings(
                RESTCLIENTS_CANVAS_HOST=origin):

            self.assertEquals(allow_origin(
                'https://canvas.edu'), origin)
            self.assertEquals(allow_origin(
                'https://canvas.edu/courses/12345/files'), origin)
            self.assertEquals(allow_origin(
                'http://canvas.edu'), origin)
            self.assertEquals(allow_origin(
                'https://canvas.com'), origin)
            self.assertEquals(allow_origin(
                'https://www.abc.edu'), origin)
