from django.conf import settings
from blti.views.rest_dispatch import RESTDispatch
from restclients.canvas.roles import Roles
from restclients.exceptions import DataFailureException


class CanvasAccountCourseRoles(RESTDispatch):
    """ Performs actions on a Canvas account course roles
        GET returns 200 with account course roles.
    """
    def GET(self, request, **kwargs):
        roles = []
        account_id = kwargs['canvas_account_id']
        for r in Roles().get_effective_course_roles_in_account(account_id):
            roles.append(r.label)

        return self.json_response({'roles': roles})
