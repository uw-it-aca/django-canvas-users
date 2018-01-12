from restclients_core.exceptions import DataFailureException
from sis_provisioner.dao.canvas import get_course_roles_in_account
from canvas_users.views import UserRESTDispatch


class CanvasAccountCourseRoles(UserRESTDispatch):
    """ Performs actions on a Canvas account course roles
        GET returns 200 with account course roles.
    """
    def get(self, request, *args, **kwargs):
        roles = []
        account_id = kwargs['canvas_account_id']

        try:
            for r in get_course_roles_in_account(account_id):
                roles.append({
                    'role': r.label,
                    'id': r.role_id,
                    'base': r.base_role_type
                })

            return self.json_response({'roles': roles})

        except DataFailureException as err:
            return self.error_response(500, err.msg)
        except Exception as err:
            return self.error_response(500, err)
