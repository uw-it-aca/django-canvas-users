# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from django.test import TestCase, override_settings
from canvas_users.models import AddUserManager, AddUser, AddUsersImport
from canvas_users.dao.canvas import *
from canvas_users.dao.sis_provisioner import validate_logins
from uw_canvas.models import CanvasCourse, CanvasRole
import mock


class CanvasDAOTest(TestCase):
    def setUp(self):
        class MockCanvasData:
            def __init__(self, *args, **kwargs):
                self.account_sis_id = ''
                self.is_canvas_administrator = False
                self.is_instructor = False
                self.is_teaching_assistant = False
                self.is_designer = False

                for key, value in kwargs.items():
                    setattr(self, key, value)

        self.canvas_data = MockCanvasData
        self.canvas_roles = [
            CanvasRole(role_id=1,
                       label='Student',
                       base_role_type='StudentEnrollment'),
            CanvasRole(role_id=2,
                       label='TA',
                       base_role_type='TaEnrollment'),
            CanvasRole(role_id=3,
                       label='Teacher',
                       base_role_type='TeacherEnrollment'),
            CanvasRole(role_id=4,
                       label='Observer',
                       base_role_type='ObserverEnrollment'),
            CanvasRole(role_id=5,
                       label='Designer',
                       base_role_type='DesignerEnrollment'),
        ]

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
        self.assertEqual(valid_group_section(
            '2013-spring-TRAIN-101-A'), False)
        self.assertEqual(valid_group_section(
            None), False)
        self.assertEqual(valid_group_section(
            '2013-spring-TRAIN-101-A-groups'), True)
        self.assertEqual(valid_group_section(
            'course_12345-groups'), True)

    @mock.patch.object(Roles, 'get_effective_course_roles_in_account')
    @override_settings(RESTCLIENTS_CANVAS_ACCOUNT_ID='12345',
                       CONTINUUM_CANVAS_ACCOUNT_ID='50000',
                       STUDENT_ROLE_DISALLOWED_SUBACCOUNTS=['uwcourse'])
    def test_get_course_roles_in_account(self, mock_method):
        mock_method.return_value = self.canvas_roles

        # subaccount permits adding student role
        r1 = get_course_roles_in_account(self.canvas_data(is_instructor=True))
        mock_method.assert_called_with('12345')
        self.assertEqual(r1, [
            {'base': 'StudentEnrollment', 'id': 1, 'role': 'Student'},
            {'base': 'TaEnrollment', 'id': 2, 'role': 'TA'},
            {'base': 'TeacherEnrollment', 'id': 3, 'role': 'Teacher'},
            {'base': 'ObserverEnrollment', 'id': 4, 'role': 'Observer'},
            {'base': 'DesignerEnrollment', 'id': 5, 'role': 'Designer'},
        ])

        r2 = get_course_roles_in_account(self.canvas_data(
            is_teaching_assistant=True))
        mock_method.assert_called_with('12345')
        self.assertEqual(r2, [
            {'base': 'StudentEnrollment', 'id': 1, 'role': 'Student'},
            {'base': 'ObserverEnrollment', 'id': 4, 'role': 'Observer'},
        ])

        # subaccount does not permit adding student role
        r3 = get_course_roles_in_account(self.canvas_data(
            account_sis_id='uwcourse:abc', is_teaching_assistant=True))
        mock_method.assert_called_with('12345')
        self.assertEqual(r3, [
            {'base': 'ObserverEnrollment', 'id': 4, 'role': 'Observer'},
        ])

        r4 = get_course_roles_in_account(self.canvas_data(
            account_sis_id='uwcourse:abc', is_designer=True))
        mock_method.assert_called_with('12345')
        self.assertEqual(r4, [
            {'base': 'DesignerEnrollment', 'id': 5, 'role': 'Designer'},
        ])

        r5 = get_course_roles_in_account(self.canvas_data(
            account_sis_id='uwcourse:abc', is_instructor=True))
        mock_method.assert_called_with('12345')
        self.assertEqual(r5, [
            {'base': 'TaEnrollment', 'id': 2, 'role': 'TA'},
            {'base': 'TeacherEnrollment', 'id': 3, 'role': 'Teacher'},
            {'base': 'ObserverEnrollment', 'id': 4, 'role': 'Observer'},
            {'base': 'DesignerEnrollment', 'id': 5, 'role': 'Designer'},
        ])

        # subaccount does not permit adding student role, user is admin
        r6 = get_course_roles_in_account(self.canvas_data(
            account_sis_id='uwcourse:uweo:abc', is_canvas_administrator=True))
        mock_method.assert_called_with('50000')
        self.assertEqual(r6, [
            {'base': 'StudentEnrollment', 'id': 1, 'role': 'Student'},
            {'base': 'TaEnrollment', 'id': 2, 'role': 'TA'},
            {'base': 'TeacherEnrollment', 'id': 3, 'role': 'Teacher'},
            {'base': 'ObserverEnrollment', 'id': 4, 'role': 'Observer'},
            {'base': 'DesignerEnrollment', 'id': 5, 'role': 'Designer'},
        ])


class AddUserManagerTest(TestCase):
    @mock.patch('canvas_users.models.validate_logins')
    @mock.patch.object(Users, 'get_users_for_course')
    def test_users_in_course(self, mock_method, mock_validate):
        mock_method.return_value = []
        mock_validate.return_value = []
        r = AddUser.objects.users_in_course(
            '2013-spring-TRAIN-101-A', '2013-spring-TRAIN-101-AA', 'student',
            logins=[])
        self.assertEqual(len(r), 0)

    def test_user_in_section(self):
        pass

    def test_get_existing_role(self):
        pass

    def test_format_role(self):
        self.assertEqual(AddUserManager()._format_role(
            'TeacherEnrollment'), 'Teacher')


class AddUsersImportTest(TestCase):
    def test_progress(self):
        self.assertEqual(AddUsersImport(
            imported=100, importing=100).progress(), 100)
        self.assertEqual(AddUsersImport(
            imported=35, importing=35).progress(), 100)
        self.assertEqual(AddUsersImport(
            imported=0, importing=50).progress(), 0)
        self.assertEqual(AddUsersImport(
            imported=2, importing=7).progress(), 28)
        self.assertEqual(AddUsersImport(
            imported=9, importing=12).progress(), 75)
