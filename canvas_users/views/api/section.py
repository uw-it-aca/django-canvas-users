from restclients.canvas.sections import Sections
from restclients.canvas.courses import Courses
from canvas_users.views.api.rest_dispatch import UserRESTDispatch
from blti import BLTI
import re


class CanvasCourseSections(UserRESTDispatch):
    """ Performs actions on Canvas Course Sections
        GET returns 200 with course sections.
    """
    def GET(self, request, **kwargs):
        sections = []
        course_id = kwargs['canvas_course_id']
        importer_id = BLTI().get_session(request)['custom_canvas_user_id']

        for s in Sections(as_user=importer_id).get_sections_in_course(course_id):
            if not (s.sis_section_id and re.match(r'.*-groups$', s.sis_section_id)):
                sections.append({
                    'id': s.section_id,
                    'sis_id': s.sis_section_id,
                    'name': s.name
                })

        if not len(sections):
            sections.append({
                'id': 0,
                'sis_id': '',
                'name': Courses(as_user=importer_id).get_course(course_id).name
            })

        return self.json_response({'sections': sorted(sections, key=lambda k: k['name'])})
