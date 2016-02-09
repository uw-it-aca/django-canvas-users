from django.conf import settings
from django.template import Context, loader
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from blti import BLTI, BLTIException
from restclients.canvas.roles import Roles
from restclients.exceptions import DataFailureException
from sis_provisioner.policy import CoursePolicy, CoursePolicyException
import json


@csrf_exempt
def CanvasUsers(request, template='canvas_users/launch_add_user.html'):
    blti_data = {"context_label": "NO COURSE"}
    validation_error = None
    sis_course_id = 'None'
    canvas_course_id = 'None'
    account_id = 'None'
    status_code = 200
    policy = CoursePolicy()

    try:
        blti = BLTI()
        blti_data = blti.validate(request, visibility=BLTI.ADMIN)
        canvas_login_id = blti_data.get('custom_canvas_user_login_id')
        canvas_course_id = blti_data.get('custom_canvas_course_id')
        sis_course_id = blti_data.get('lis_course_offering_sourcedid',
                                      policy.adhoc_sis_id(canvas_course_id))
        account_id = blti_data.get('custom_canvas_account_id')
        canvas_host = blti_data.get('custom_canvas_api_domain')

        blti_data['user_id'] = canvas_login_id
        blti.set_session(request, **blti_data)

    except (BLTIException, CoursePolicyException) as err:
        validation_error = err
        status_code = 401
        template = 'blti/401.html'
    except DataFailureException as err:
        validation_error = err
        status_code = 500
    except Exception as err:
        validation_error = err
        status_code = 400

    t = loader.get_template(template)
    c = Context({
        'SIS_COURSE_ID': sis_course_id,
        'CANVAS_COURSE_ID': canvas_course_id,
        'CANVAS_ACCOUNT_ID': account_id,
        'CANVAS_HOSTNAME': canvas_host,
        'session_id': request.session.session_key,
        'blti_json': json.dumps(blti_data),
        'VALIDATION_ERROR': validation_error,
        'HTTP_HOST': request.META['HTTP_HOST']
    })

    return HttpResponse(t.render(c), status=status_code)


def CanvasAddUsers(request, template='canvas_users/add_user.html'):
    blti_data = {"context_label": "NO COURSE"}
    validation_error = None
    sis_course_id = 'None'
    canvas_host = None
    canvas_course_id = 'None'
    account_id = 'None'
    status_code = 200
    policy = CoursePolicy()

    try:
        blti_data = BLTI().get_session(request)
        canvas_login_id = blti_data.get('custom_canvas_user_login_id')
        canvas_course_id = blti_data.get('custom_canvas_course_id')
        sis_course_id = blti_data.get('lis_course_offering_sourcedid',
                                      policy.adhoc_sis_id(canvas_course_id))
        account_id = blti_data.get('custom_canvas_account_id')
        canvas_host = blti_data.get('custom_canvas_api_domain')

    except BLTIException as err:
        if request.method != 'OPTIONS':
            validation_error = err
            status_code = 401
            template = 'blti/401.html'
    except DataFailureException as err:
        validation_error = err
        status_code = 500
    except Exception as err:
        validation_error = err
        status_code = 400

    t = loader.get_template(template)
    c = Context({
        'SIS_COURSE_ID': sis_course_id,
        'CANVAS_COURSE_ID': canvas_course_id,
        'CANVAS_ACCOUNT_ID': account_id,
        'CANVAS_HOSTNAME': canvas_host,
        'HTTP_HOST': request.META['HTTP_HOST'],
        'session_id': request.session.session_key,
        'blti_json': json.dumps(blti_data),
        'VALIDATION_ERROR': validation_error
    })

    response = HttpResponse(t.render(c), status=status_code)
    if request.method == 'OPTIONS':
        response['Access-Control-Allow-Origin'] = "*"
        response['Access-Control-Allow-Methods'] = "POST, GET"
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-SessionId, X-CSRFToken, X-CSRF-Token, X-Requested-With'

    response['Access-Control-Allow-Origin'] = ('https://%s' % canvas_host) if canvas_host else settings.RESTCLIENTS_CANVAS_HOST
    return response
