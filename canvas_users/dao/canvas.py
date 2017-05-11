from uw_canvas.users import Users
from uw_canvas.enrollments import Enrollments
from uw_canvas.sections import Sections
#from sis_provisioner.util.retry import retry
from sis_provisioner.dao.course import valid_academic_course_sis_id
from sis_provisioner.exceptions import CoursePolicyException
from canvas_users.exceptions import MissingSectionException
#from urllib3.exceptions import SSLError
from logging import getLogger
import re


logger = getLogger(__name__)

RE_GROUP_SECTION = re.compile(r'.*-groups$')


#@retry(SSLError, tries=3, delay=1, logger=logger)
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


#@retry(SSLError, tries=3, delay=1, logger=logger)
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
        try:
            valid_academic_course_sis_id(course.sis_course_id)
            raise MissingSectionException(
                'Adding users to this course not allowed')
        except CoursePolicyException:
            sections.append({'id': 0, 'sis_id': '', 'name': course.name})

    return sections


def valid_group_section(sis_section_id):
    return True if (
        sis_section_id is not None and
        RE_GROUP_SECTION.match(str(sis_section_id)) is not None) else False
