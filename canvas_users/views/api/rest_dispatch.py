from django.conf import settings
from blti.views.rest_dispatch import RESTDispatch
from django.views.decorators.csrf import csrf_exempt


class UserRESTDispatch(RESTDispatch):
    extra_response_headers = {
        'Access-Control-Allow-Methods': "POST, GET",
        'Access-Control-Allow-Headers': 'Content-Type, X-SessionId, X-CSRFToken, X-CSRF-Token, X-Requested-With',
        'Access-Control-Allow-Origin': settings.RESTCLIENTS_CANVAS_HOST
    }

    @csrf_exempt
    def run(self, *args, **named_args):
        return super(UserRESTDispatch, self).run(*args, **named_args)

    def OPTIONS(self, request, **kwargs):
        return self._http_response(200)
