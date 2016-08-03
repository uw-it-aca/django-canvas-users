from django.conf import settings
from django.http import HttpResponse
from blti.views import BLTIView, BLTILaunchView
from blti import BLTIException
from sis_provisioner.policy import CoursePolicy
import re


def allow_origin(request):
    canvas_host = getattr(settings, 'RESTCLIENTS_CANVAS_HOST')
    origin = request.META.get('HTTP_ORIGIN', '')
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
        blti_data = kwargs.get('blti_params')

        return {
            'canvas_hostname': blti_data.get('custom_canvas_api_domain'),
            'session_id': request.session.session_key,
            'http_host': request.META['HTTP_HOST']
        }


class AddUsersView(BLTIView):
    template_name = 'canvas_users/add_user.html'

    def get_context_data(self, **kwargs):
        request = kwargs.get('request')
        blti_data = kwargs.get('blti_params')
        canvas_course_id = blti_data.get('custom_canvas_course_id')

        context = {
            'sis_course_id': blti_data.get(
                'lis_course_offering_sourcedid',
                CoursePolicy().adhoc_sis_id(canvas_course_id)),
            'canvas_course_id': canvas_course_id,
            'canvas_account_id': blti_data.get('custom_canvas_account_id'),
            'canvas_hostname': blti_data.get('custom_canvas_api_domain'),
            'session_id': request.session.session_key,
            'http_host': request.META['HTTP_HOST']
        }
        return context

    def add_headers(self, **kwargs):
        request = kwargs.get('request')
        response = kwargs.get('response')
        blti_data = kwargs.get('blti_params', None)
        if blti_data is not None:
            canvas_host = 'https://%s' % blti_data.get(
                'custom_canvas_api_domain')
        else:
            canvas_host = allow_origin(request)

        response['Access-Control-Allow-Methods'] = 'POST, GET'
        response['Access-Control-Allow-Headers'] = ', '.join(
            ['Content-Type', 'X-SessionId', 'X-CSRFToken', 'X-CSRF-Token',
             'X-Requested-With'])
        response['Access-Control-Allow-Origin'] = canvas_host

    def options(self, *args, **kwargs):
        response = HttpResponse('GET')
        self.add_headers(request=args[0], response=response, **kwargs)
        return response
