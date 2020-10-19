from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from blti.views import BLTIView, BLTILaunchView, RESTDispatch
from blti import BLTIException
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


def add_headers_for_view(view, **kwargs):
    if hasattr(view, 'blti'):
        canvas_host = 'https://{}'.format(view.blti.canvas_api_domain)
    else:
        http_origin = view.request.META.get('HTTP_ORIGIN', '')
        canvas_host = allow_origin(http_origin)

    response = kwargs.get('response')
    response['Access-Control-Allow-Methods'] = ', '.join(
        view._allowed_methods())
    response['Access-Control-Allow-Headers'] = ', '.join([
        'Content-Type', 'X-SessionId', 'X-CSRFToken', 'X-CSRF-Token',
        'X-Requested-With'])
    response['Access-Control-Allow-Origin'] = canvas_host

    if view.request.method == 'OPTIONS':
        response['Allow'] = ', '.join(view._allowed_methods())
        response['Content-Length'] = '0'


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
            course_sis_id = 'course_{}'.format(canvas_course_id)

        return {
            'sis_course_id': course_sis_id,
            'canvas_course_id': canvas_course_id,
            'canvas_account_id': self.blti.canvas_account_id,
            'canvas_hostname': self.blti.canvas_api_domain,
            'session_id': self.request.session.session_key,
            'http_host': self.request.META['HTTP_HOST']
        }

    def add_headers(self, **kwargs):
        add_headers_for_view(self, **kwargs)

    def options(self, request, *args, **kwargs):
        return self.render_to_response({})


class UserRESTDispatch(RESTDispatch):
    authorized_role = 'admin'

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(UserRESTDispatch, self).dispatch(request, *args, **kwargs)

    def options(self, request, *args, **kwargs):
        return self.json_response(status=200)

    def add_headers(self, **kwargs):
        add_headers_for_view(self, **kwargs)
