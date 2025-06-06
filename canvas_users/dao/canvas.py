# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from uw_canvas.users import Users
from uw_canvas.enrollments import Enrollments
from uw_canvas.sections import Sections
from uw_canvas.roles import Roles
from uw_canvas.models import CanvasCourse, CanvasUser
from canvas_users.exceptions import MissingSectionException
from logging import getLogger
import re


logger = getLogger(__name__)

RE_GROUP_SECTION = re.compile(r'.*-groups$')


def get_user_by_sis_id(sis_user_id):
    return Users().get_user_by_sis_id(sis_user_id)


def get_course_users(course_id):
    return Users().get_users_for_course(
        course_id, params={'per_page': 1000, 'include': ['enrollments']})


def create_user(**kwargs):
    return Users().create_user(CanvasUser(**kwargs))


def enroll_course_user(**kwargs):
    params = {
        'role_id': kwargs.get('role_id'),
        'limit_privileges_to_course_section': kwargs.get('section_only'),
        'notify': kwargs.get('notify_users'),
        'enrollment_state': 'active'}

    if int(kwargs.get('section_id', 0)) > 0:
        params['course_section_id'] = kwargs.get('section_id')

    return Enrollments(as_user=kwargs.get('as_user')).enroll_user(
        kwargs.get('course_id'), kwargs.get('user_id'),
        kwargs.get('role_type'), params=params)


def get_course_sections(course, user_id):
    sections = []
    canvas = Sections(as_user=user_id)
    for section in canvas.get_sections_in_course(course.course_id):
        if not valid_group_section(section.sis_section_id):
            sections.append({
                'id': section.section_id,
                'sis_id': section.sis_section_id,
                'name': section.name
            })

    if not len(sections):
        canvas_course = CanvasCourse(sis_course_id=course.sis_course_id)
        if canvas_course.is_academic_sis_id():
            raise MissingSectionException(
                'Adding users to this course not allowed')
        else:
            sections.append({'id': 0, 'sis_id': '', 'name': course.name})

    return sections


def get_course_roles_in_account(canvas_data):
    def _is_permitted(role_type):
        return any(
            [_can_assign_role_type(
                role_type, adder_role) for adder_role in adder_roles])

    def _can_assign_role_type(role_type, adder_role):
        return adder_role.permissions.get(
            f"add_{_label(role_type)}_to_course", {}).get('enabled', True)

    def _label(role_type):
        return role_type.removesuffix('Enrollment').lower()

    base_role_types = [
        'StudentEnrollment', 'TeacherEnrollment', 'TaEnrollment',
        'ObserverEnrollment', 'DesignerEnrollment']

    account_id = canvas_data.canvas_account_id
    all_course_roles = Roles().get_roles_in_account(
        account_id, {'show_inherited': '1', 'per_page': 100})

    try:
        adder_role_labels = list(
            map(_label, canvas_data.user_roles.split(',')))
    except AttributeError:
        adder_role_labels = [r for (r, permitted) in [
            ('account admin', canvas_data.is_canvas_administrator),
            ('teacher', canvas_data.is_instructor),
            ('ta', canvas_data.is_teaching_assistant),
            ('designer', canvas_data.is_designer)] if permitted]

    adder_roles = [r for r in all_course_roles if (
        r.label.lower() in adder_role_labels)]

    permitted_role_types = [t for t in base_role_types if _is_permitted(t)]

    return [{
        'role': added_role.label,
        'id': added_role.role_id,
        'base': added_role.base_role_type
    } for added_role in all_course_roles if (
        added_role.base_role_type in permitted_role_types)]


def valid_group_section(sis_section_id):
    return True if (
        sis_section_id is not None and
        RE_GROUP_SECTION.match(str(sis_section_id)) is not None) else False
