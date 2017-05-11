from django.test import TestCase
from canvas_users.models import AddUserManager, AddUser, AddUsersImport
from canvas_users.views import allow_origin
from canvas_users.dao.canvas import *
from uw_canvas.models import CanvasCourse
import mock


class CanvasDAOTest(TestCase):
    @mock.patch.object(Users, 'get_users_for_course')
    def test_get_course_users(self, mock_method):
        r = get_course_users('123')
        mock_method.assert_called_with(
            '123', params={'per_page': 1000, 'include': ['enrollments']})

    @mock.patch('canvas_users.dao.canvas.Enrollments')
    def test_enrollments_constructor(self, mock_object):
        r = enroll_course_user(as_user='123')
        mock_object.assert_called_with(as_user='123')

    @mock.patch.object(Enrollments, 'enroll_user')
    def test_enroll_course_user(self, mock_method):
        r = enroll_course_user(
            role_id='1', section_only=True, notify_users=False, section_id='2',
            as_user='3', course_id='4', user_id='5', role_type='abc')
        mock_method.assert_called_with('4', '5', 'abc', params={
            'enrollment_state': 'active', 'course_section_id': '2',
            'notify': False, 'limit_privileges_to_course_section': True,
            'role_id': '1'})

        r = enroll_course_user(
            role_id='1', section_only=True, notify_users=False,
            as_user='3', course_id='4', user_id='5', role_type='abc')
        mock_method.assert_called_with('4', '5', 'abc', params={
            'enrollment_state': 'active', 'notify': False,
            'limit_privileges_to_course_section': True, 'role_id': '1'})

    @mock.patch('canvas_users.dao.canvas.Sections')
    def test_sections_constructor(self, mock_object):
        course = CanvasCourse(course_id='123', sis_course_id='789', name='xyz')
        r = get_course_sections(course, '456')
        mock_object.assert_called_with(as_user='456')

    @mock.patch.object(Sections, 'get_sections_in_course')
    def test_get_course_sections(self, mock_method):
        course = CanvasCourse(course_id='123', sis_course_id='789', name='xyz')
        r = get_course_sections(course, '456')
        mock_method.assert_called_with('123')

    def test_valid_group_section(self):
        self.assertEquals(valid_group_section(
            '2013-spring-TRAIN-101-A'), False)
        self.assertEquals(valid_group_section(
            None), False)
        self.assertEquals(valid_group_section(
            '2013-spring-TRAIN-101-A-groups'), True)
        self.assertEquals(valid_group_section(
            'course_12345-groups'), True)


class AddUserManagerTest(TestCase):
    def test_user_in_section(self):
        pass

    def test_get_existing_role(self):
        pass

    def test_normalize_list(self):
        with self.settings(
                ADD_USER_DOMAIN_WHITELIST=['abc.com', 'xyz.edu']):
            self.assertEquals(len(AddUserManager()._normalize_list(
                ['joe@abc.com', 'joe@abc.com', 'joe@abc.com'])), 1)
            self.assertEquals(len(AddUserManager()._normalize_list(
                ['joe@abc.com', 'joe@xyz.edu', 'joe@abc.edu'])), 2)
            self.assertEquals(len(AddUserManager()._normalize_list(
                ['joe@abc.com', 'joe@xyz.com', 'joe@abc.edu'])), 3)

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
