from restclients.canvas.sections import Sections
from restclients.canvas.courses import Courses
from restclients.util.retry import retry
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
        sections = []
        course_id = kwargs['canvas_course_id']
        user_id = BLTI().get_session(request)['custom_canvas_user_id']

        @retry(SSLError, tries=3, delay=1, logger=logger)
        def _get_sections(course_id, user_id):
            return Sections(as_user=user_id).get_sections_in_course(course_id)

        for s in _get_sections(course_id, user_id):
            if not (s.sis_section_id and
                    re.match(r'.*-groups$', s.sis_section_id)):
                sections.append({
                    'id': s.section_id,
                    'sis_id': s.sis_section_id,
                    'name': s.name
                })

        if not len(sections):
            courses_api = Courses(as_user=user_id)
            sections.append({
                'id': 0,
                'sis_id': '',
                'name': courses_api.get_course(course_id).name
            })

        return self.json_response({
            'sections': sorted(sections, key=lambda k: k['name'])
        })
