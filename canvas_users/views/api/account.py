# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from restclients_core.exceptions import DataFailureException
from canvas_users.dao.canvas import get_course_roles_in_account
from canvas_users.views import UserRESTDispatch


class CanvasAccountCourseRoles(UserRESTDispatch):
    """ Performs actions on a Canvas account course roles
        GET returns 200 with account course roles.
    """
    def get(self, request, *args, **kwargs):
        try:
            role_data = get_course_roles_in_account(
                self.blti.account_sis_id, self.blti.roles)
            return self.json_response({'roles': role_data})

        except DataFailureException as err:
            return self.error_response(500, err.msg)
        except Exception as err:
            return self.error_response(500, err)
