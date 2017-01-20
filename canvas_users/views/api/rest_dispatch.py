from django.conf import settings
from blti.views.rest_dispatch import RESTDispatch
from django.views.decorators.csrf import csrf_exempt
from canvas_users.views import allow_origin


class UserRESTDispatch(RESTDispatch):
    @csrf_exempt
    def run(self, *args, **named_args):
        request = args[0]
        self._set_response_headers(request)
        if request.method == 'OPTIONS':
            return self.OPTIONS(*args, **named_args)

        return super(UserRESTDispatch, self).run(*args, **named_args)

    def OPTIONS(self, *args, **named_args):
        return self._http_response('', status=200)

    def _set_response_headers(self, request):
        origin = request.META.get('HTTP_ORIGIN', '')
        self.extra_response_headers = {
            'Access-Control-Allow-Methods': "POST, GET",
            'Access-Control-Allow-Headers': 'Content-Type, X-SessionId, '
                                            'X-CSRFToken, X-CSRF-Token, '
                                            'X-Requested-With',
            'Access-Control-Allow-Origin': allow_origin(origin)
        }
