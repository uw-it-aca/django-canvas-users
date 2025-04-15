# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from uw_canvas.models import CanvasCourse
from restclients_core.exceptions import DataFailureException
from canvas_users.dao.canvas import get_course_sections
from canvas_users.exceptions import MissingSectionException
from canvas_users.views import UserRESTDispatch
import traceback
import logging


logger = logging.getLogger(__name__)


class CanvasCourseSections(UserRESTDispatch):
    """ Performs actions on Canvas Course Sections
        GET returns 200 with course sections.
    """
    def get(self, request, *args, **kwargs):
        course_id = kwargs['canvas_course_id']
        user_id = self.blti.canvas_user_id
        course_name = self.blti.course_long_name
        sis_course_id = self.blti.course_sis_id
        logging.debug(f"Course ID: {course_id}, User ID: {user_id}, "
                      f"Course Name: {course_name}, "
                      f"SIS Course ID: {sis_course_id}, "
                      f"Request: {request}")

        try:
            course = CanvasCourse(course_id=course_id,
                                  sis_course_id=sis_course_id,
                                  name=course_name)
            logger.debug(f"Course: {course}")
            sections = get_course_sections(course, user_id)
            logger.debug(f"Sections: {sections}")

        except MissingSectionException as err:
            msg = 'Adding users to this course not allowed'
            return self.error_response(401, message=msg)
        except DataFailureException as err:
            if err.status == 404:
                msg = 'Course not found'
                return self.error_response(404, message=msg)
            elif err.status == 403:
                msg = 'You do not have permission to access this course'
                return self.error_response(403, message=msg)

            logger.error(f"sections: DataFailureException: {err}")
            return self.error_response(500, message=err.msg)
        except Exception as err:
            logger.exception(f"sections: Exception: {err}")
            return self.error_response(500, message=traceback.format_exc(err))

        return self.json_response({
            'sections': sorted(sections, key=lambda k: k['name'])
        })
