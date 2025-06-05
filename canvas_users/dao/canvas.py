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
    role_labels = ['Student', 'Teacher', 'TA', 'Observer', 'Designer']
    adder_roles = [('Teacher', canvas_data.is_instructor),
                   ('TA', canvas_data.is_teaching_assistant),
                   ('Designer', canvas_data.is_designer)]
    account_id = canvas_data.canvas_account_id
    course_roles = {r.label: r for r in Roles().get_roles_in_account(
        account_id)}

    def _is_permitted(added_role):
        return canvas_data.is_canvas_administrator or any(
            [context_role and _can_assign_role(
                adder_role, added_role) for (
                    adder_role, context_role) in adder_roles])

    def _can_assign_role(adder_role_label, added_role_label):
        try:
            adder_role_id = course_roles[adder_role_label].role_id
            adder_role = Roles().get_role(account_id, adder_role_id)
            return adder_role.permissions.get(
                f"add_{added_role_label.lower()}_to_course", {}).get(
                    'enabled', True)
        except IndexError:
            logger.error(f"{adder_role_label} not found in course roles")
            return True

    def _base_role(role_label):
        return f"{role_label.capitalize()}Enrollment"

    roles_permitted = {_base_role(r): _is_permitted(r) for r in role_labels}
    roles = []
    for r in Roles().get_effective_course_roles_in_account(account_id):
        if roles_permitted.get(r.base_role_type, True):
            roles.append({
                'role': r.label,
                'id': r.role_id,
                'base': r.base_role_type,
            })

    return roles


def valid_group_section(sis_section_id):
    return True if (
        sis_section_id is not None and
        RE_GROUP_SECTION.match(str(sis_section_id)) is not None) else False
