# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from restclients_core.exceptions import DataFailureException
from canvas_users.dao.canvas import get_course_roles_in_account
from canvas_users.views import UserRESTDispatch
from logging import getLogger


logger = getLogger(__name__)


class CanvasAccountCourseRoles(UserRESTDispatch):
    """ Performs actions on a Canvas account course roles
        GET returns 200 with account course roles.
    """
    def get(self, request, *args, **kwargs):
        try:
            role_data = get_course_roles_in_account(self.blti)
            return self.json_response({'roles': role_data})

        except DataFailureException as err:
            if err.status == 404:
                msg = 'Course not found'
                return self.error_response(404, message=msg)
            elif err.status == 403:
                msg = 'You do not have permission to access this course'
                return self.error_response(403, message=msg)

            logger.error(f"roles: DataFailureException: {err}")
            return self.error_response(500, message=err.msg)
        except Exception as err:
            logger.exception(f"roles: Exception: {err}")
            return self.error_response(500, err)
