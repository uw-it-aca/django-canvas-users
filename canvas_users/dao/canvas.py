# Copyright 2023 UW-IT, University of Washington
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


def get_course_roles_in_account(account_sis_id):
    if account_sis_id.startswith('uwcourse:uweo'):
        account_id = getattr(settings, 'CONTINUUM_CANVAS_ACCOUNT_ID')
    else:
        account_id = getattr(settings, 'RESTCLIENTS_CANVAS_ACCOUNT_ID')

    return Roles().get_effective_course_roles_in_account(account_id)


def valid_group_section(sis_section_id):
    return True if (
        sis_section_id is not None and
        RE_GROUP_SECTION.match(str(sis_section_id)) is not None) else False
