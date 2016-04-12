from restclients.canvas.sections import Sections
from restclients.canvas.courses import Courses
from restclients.util.retry import retry
from restclients.exceptions import DataFailureException
from sis_provisioner.policy import CoursePolicy, CoursePolicyException
from canvas_users.views.api.rest_dispatch import UserRESTDispatch
from urllib3.exceptions import SSLError
from blti import BLTI
import logging
import re


logger = logging.getLogger(__name__)


class CanvasCourseSections(UserRESTDispatch):
    """ Performs actions on Canvas Course Sections
        GET returns 200 with course sections.
    """
    def GET(self, request, **kwargs):
        blti_session = BLTI().get_session(request)
        sections = []
        course_id = kwargs['canvas_course_id']
        user_id = blti_session['custom_canvas_user_id']
        course_sis_id = blti_session.get('lis_course_offering_sourcedid', None)

        @retry(SSLError, tries=3, delay=1, logger=logger)
        def _get_sections(course_id, user_id):
            return Sections(as_user=user_id).get_sections_in_course(course_id)

        try:
            for s in _get_sections(course_id, user_id):
                if not (s.sis_section_id and
                        re.match(r'.*-groups$', s.sis_section_id)):
                    sections.append({
                        'id': s.section_id,
                        'sis_id': s.sis_section_id,
                        'name': s.name
                    })

            if not len(sections):
                try:
                    CoursePolicy().valid_academic_course_sis_id(course_sis_id)
                    return self.error_response(
                        400, 'Course contains no sections')
                except CoursePolicyException:
                    courses_api = Courses(as_user=user_id)
                    sections.append({
                        'id': 0,
                        'sis_id': '',
                        'name': courses_api.get_course(course_id).name
                    })

        except DataFailureException as err:
            return self.error_response(500, err.msg)
        except Exception as err:
            return self.error_response(500, err)

        return self.json_response({
            'sections': sorted(sections, key=lambda k: k['name'])
        })
