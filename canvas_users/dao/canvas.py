from restclients.canvas.users import Users
from restclients.canvas.enrollments import Enrollments
from restclients.canvas.sections import Sections
from restclients.util.retry import retry
from urllib3.exceptions import SSLError
from logging import getLogger
import re


logger = getLogger(__name__)

RE_GROUP_SECTION = re.compile(r'.*-groups$')


@retry(SSLError, tries=3, delay=1, logger=logger)
def get_course_users(course_id):
    return Users().get_users_for_course(
        course_id, params={'per_page': 1000, 'include': ['enrollments']})


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


@retry(SSLError, tries=3, delay=1, logger=logger)
def get_course_sections(course_id, user_id):
    return Sections(as_user=user_id).get_sections_in_course(course_id)


def valid_group_section(sis_section_id):
    return True if (sis_section_id is not None and
        RE_GROUP_SECTION.match(str(sis_section_id)) is not None) else False
