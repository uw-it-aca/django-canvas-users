from restclients.canvas.roles import Roles
from restclients.exceptions import DataFailureException
from canvas_users.views.api.rest_dispatch import UserRESTDispatch


class CanvasAccountCourseRoles(UserRESTDispatch):
    """ Performs actions on a Canvas account course roles
        GET returns 200 with account course roles.
    """
    def GET(self, request, **kwargs):
        roles = []
        account_id = kwargs['canvas_account_id']
        for r in Roles().get_effective_course_roles_in_account(account_id):
            roles.append({'role': r.label, 'id': r.role_id, 'base': r.base_role_type})

        return self.json_response({'roles': roles})
