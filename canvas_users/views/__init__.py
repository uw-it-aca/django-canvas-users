# Copyright 2026 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from blti.views import BLTILaunchView, BLTIView, RESTDispatch
from django.views.decorators.csrf import csrf_exempt


class LaunchView(BLTILaunchView):
    template_name = 'canvas_users/launch_add_user.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        return {
            'canvas_hostname': self.blti.canvas_api_domain,
            'session_id': self.request.session.session_key,
            'http_host': self.request.META['HTTP_HOST']
        }


class AddUsersView(BLTIView):
    template_name = 'canvas_users/add_user.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        canvas_course_id = self.blti.canvas_course_id

        if self.blti.course_sis_id:
            course_sis_id = self.blti.course_sis_id
        else:
            course_sis_id = f'course_{canvas_course_id}'

        return {
            'sis_course_id': course_sis_id,
            'canvas_course_id': canvas_course_id,
            'sis_account_id': self.blti.account_sis_id,
            'canvas_account_id': self.blti.canvas_account_id,
            'canvas_hostname': self.blti.canvas_api_domain,
            'session_id': self.request.session.session_key,
            'http_host': self.request.META['HTTP_HOST']
        }

    def options(self, request, *args, **kwargs):
        return self.render_to_response({})


class UserRESTDispatch(RESTDispatch):
    authorized_role = 'admin'

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
