from restclients.exceptions import DataFailureException
from sis_provisioner.exceptions import CoursePolicyException
from sis_provisioner.dao.course import valid_academic_course_sis_id
from canvas_users.dao.canvas import get_course_sections, valid_group_section
from canvas_users.views.api.rest_dispatch import UserRESTDispatch
import traceback


class CanvasCourseSections(UserRESTDispatch):
    """ Performs actions on Canvas Course Sections
        GET returns 200 with course sections.
    """
    def GET(self, request, **kwargs):
        sections = []
        course_id = kwargs['canvas_course_id']

        blti_data = self.get_session(request)
        user_id = blti_data.get('custom_canvas_user_id')
        course_name = blti_data.get('context_title')
        course_sis_id = blti_data.get('lis_course_offering_sourcedid', '')

        try:
            for section in get_course_sections(course_id, user_id):
                if not valid_group_section(section.sis_section_id):
                    sections.append({
                        'id': section.section_id,
                        'sis_id': section.sis_section_id,
                        'name': section.name
                    })

            if not len(sections):
                try:
                    valid_academic_course_sis_id(course_sis_id)
                    return self.error_response(
                        401, 'Adding users to this course not allowed')
                except CoursePolicyException:
                    sections.append({
                        'id': 0,
                        'sis_id': '',
                        'name': course_name
                    })

        except DataFailureException as err:
            return self.error_response(500, message=err.msg)
        except Exception as err:
            return self.error_response(500, message=traceback.format_exc(err))

        return self.json_response({
            'sections': sorted(sections, key=lambda k: k['name'])
        })
