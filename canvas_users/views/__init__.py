from django.conf import settings
from django.http import HttpResponse
from blti.views import BLTIView, BLTILaunchView
from blti import BLTIException
from sis_provisioner.dao.course import adhoc_course_sis_id
import re


def allow_origin(origin):
    canvas_host = getattr(settings, 'RESTCLIENTS_CANVAS_HOST')
    if origin != canvas_host:
        m = re.match(r'^https://.*\.([a-z]+\.[a-z]+)$', origin)
        if m:
            domain = m.group(1)
            if canvas_host[-len(domain):] == domain:
                canvas_host = origin

    return canvas_host


class LaunchView(BLTILaunchView):
    template_name = 'canvas_users/launch_add_user.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        request = kwargs.get('request')

        return {
            'canvas_hostname': self.blti.canvas_api_domain,
            'session_id': request.session.session_key,
            'http_host': request.META['HTTP_HOST']
        }


class AddUsersView(BLTIView):
    http_method_names = ['get', 'options']
    template_name = 'canvas_users/add_user.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        request = kwargs.get('request')
        canvas_course_id = self.blti.canvas_course_id

        if self.blti.course_sis_id:
            course_sis_id = self.blti.course_sis_id
        else:
            course_sis_id = adhoc_course_sis_id(canvas_course_id)

        return {
            'sis_course_id': course_sis_id,
            'canvas_course_id': canvas_course_id,
            'canvas_account_id': self.blti.canvas_account_id,
            'canvas_hostname': self.blti.canvas_api_domain,
            'session_id': request.session.session_key,
            'http_host': request.META['HTTP_HOST']
        }

    def add_headers(self, **kwargs):
        response = kwargs.get('response')

        if hasattr(self, 'blti'):
            canvas_host = 'https://%s' % self.blti.canvas_api_domain
        else:
            http_origin = self.request.META.get('HTTP_ORIGIN', '')
            canvas_host = allow_origin(http_origin)

        response['Access-Control-Allow-Methods'] = 'POST, GET'
        response['Access-Control-Allow-Headers'] = ', '.join([
            'Content-Type', 'X-SessionId', 'X-CSRFToken', 'X-CSRF-Token',
            'X-Requested-With'])
        response['Access-Control-Allow-Origin'] = canvas_host

    def options(self, request, *args, **kwargs):
        return self.render_to_response({})
