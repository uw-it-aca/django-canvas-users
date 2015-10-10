from django.conf import settings
from django.template import Context, loader
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.context_processors import csrf
from blti import BLTI, BLTIException
from sis_provisioner.policy import CoursePolicy, CoursePolicyException
import json


@csrf_exempt
def Main(request, template='groups/index.html'):
    blti_data = {"context_label": "NO COURSE"}
    validation_error = None
    sis_course_id = 'None'
    canvas_course_id = 'None'
    status_code = 200
    roles = []
    policy = CoursePolicy()

    try:
        blti = BLTI()
        blti_data = blti.validate(request)
        canvas_login_id = blti_data.get('custom_canvas_user_login_id')
        canvas_course_id = blti_data.get('custom_canvas_course_id')
        policy.valid_canvas_id(canvas_course_id)
        sis_course_id = blti_data.get('lis_course_offering_sourcedid',
                                      policy.adhoc_sis_id(canvas_course_id))
        account_id = blti_data.get('custom_canvas_account_id')

        for r in Roles().get_effective_course_roles_in_account(account_id):
            roles.append(r.label)

        blti.set_session(request, user_id=canvas_login_id, course_roles=roles)

    except (BLTIException, CoursePolicyException) as err:
        validation_error = err
        status_code = 401
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
        'blti_json': json.dumps(blti_data),
        'roles': roles,
        'VALIDATION_ERROR': validation_error
    })

    c.update(csrf(request))
    return HttpResponse(t.render(c), status=status_code)
