from django.conf import settings
from blti.views import RESTDispatch
from django.views.decorators.csrf import csrf_exempt
from canvas_users.views import allow_origin


class UserRESTDispatch(RESTDispatch):
    authorized_role = 'admin'

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(UserRESTDispatch, self).dispatch(request, *args, **kwargs)

    def options(self, request, *args, **kwargs):
        return self.json_response(status=200)

    def add_headers(self, **kwargs):
        response = kwargs.get('response')
        origin = self.request.META.get('HTTP_ORIGIN', '')

        response['Access-Control-Allow-Methods'] = 'POST, GET'
        response['Access-Control-Allow-Headers'] = ', '.join([
            'Content-Type', 'X-SessionId', 'X-CSRFToken', 'X-CSRF-Token',
            'X-Requested-With'])
        response['Access-Control-Allow-Origin'] = allow_origin(origin)
