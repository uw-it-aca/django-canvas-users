from uw_canvas.models import CanvasCourse
from restclients_core.exceptions import DataFailureException
from canvas_users.dao.canvas import get_course_sections
from canvas_users.exceptions import MissingSectionException
from canvas_users.views.api.rest_dispatch import UserRESTDispatch
import traceback


class CanvasCourseSections(UserRESTDispatch):
    """ Performs actions on Canvas Course Sections
        GET returns 200 with course sections.
    """
    def GET(self, request, **kwargs):
        course_id = kwargs['canvas_course_id']
        blti_data = self.get_session(request)
        user_id = blti_data.get('custom_canvas_user_id')
        course_name = blti_data.get('context_title')
        sis_course_id = blti_data.get('lis_course_offering_sourcedid', '')

        try:
            course = CanvasCourse(course_id=course_id,
                                  sis_course_id=sis_course_id,
                                  name=course_name)
            sections = get_course_sections(course, user_id)

        except MissingSectionException as err:
            msg = 'Adding users to this course not allowed'
            return self.error_response(401, message=msg)
        except DataFailureException as err:
            return self.error_response(500, message=err.msg)
        except Exception as err:
            return self.error_response(500, message=traceback.format_exc(err))

        return self.json_response({
            'sections': sorted(sections, key=lambda k: k['name'])
        })
