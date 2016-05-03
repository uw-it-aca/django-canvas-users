from django.conf import settings
from django.http import HttpResponse
from blti.views import BLTIView, BLTILaunchView
from blti import BLTIException
from sis_provisioner.policy import CoursePolicy


class LaunchView(BLTILaunchView):
    template_name = 'canvas_users/launch_add_user.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        request = kwargs.get('request')
        blti_data = kwargs.get('blti_params')
        canvas_login_id = blti_data.get('custom_canvas_user_login_id')
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

    def options(self, request, *args, **kwargs):
        try:
            params = self.validate(request)
            canvas_host = blti_data.get('custom_canvas_api_domain')
        except BLTIException as err:
            canvas_host = getattr(settings, 'RESTCLIENTS_CANVAS_HOST', '')

        response = HttpResponse('GET')
        response['Access-Control-Allow-Origin'] = "*"
        response['Access-Control-Allow-Methods'] = "POST, GET"
        response['Access-Control-Allow-Headers'] = ', '.join(
            ['Content-Type', 'X-SessionId', 'X-CSRFToken',
             'X-CSRF-Token', 'X-Requested-With'])
        response['Access-Control-Allow-Origin'] = 'https://%s' % canvas_host
        return response
