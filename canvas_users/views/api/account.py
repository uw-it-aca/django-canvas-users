from restclients.canvas.roles import Roles
from restclients.util.retry import retry
from canvas_users.views.api.rest_dispatch import UserRESTDispatch
from urllib3.exceptions import SSLError
import logging


logger = logging.getLogger(__name__)


class CanvasAccountCourseRoles(UserRESTDispatch):
    """ Performs actions on a Canvas account course roles
        GET returns 200 with account course roles.
    """
    def GET(self, request, **kwargs):
        roles = []
        account_id = kwargs['canvas_account_id']

        @retry(SSLError, tries=3, delay=1, logger=logger)
        def _get_roles(account_id):
            return Roles().get_effective_course_roles_in_account(account_id)

        for r in _get_roles(account_id):
            roles.append({
                'role': r.label,
                'id': r.role_id,
                'base': r.base_role_type
            })

        return self.json_response({'roles': roles})
