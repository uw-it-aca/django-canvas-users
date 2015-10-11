from django.conf import settings
from blti.views.rest_dispatch import RESTDispatch
from sis_provisioner.models import User as CanvasUser
from restclients.canvas.sections import Sections
from restclients.canvas.courses import Courses
from restclients.canvas.enrollments import Enrollments
from restclients.exceptions import DataFailureException
from sis_provisioner.policy import UserPolicy, UserPolicyException
import json
import re


class ValidCanvasCourseUsers(RESTDispatch):
    """ Exposes API to manage Canvas users 
        GET returns 200 with user details
    """
    def POST(self, request, **kwargs):
        try:
            course_id = kwargs['canvas_course_id']
            data = json.loads(request.body)

            login_ids = []
            for raw_login_id in data["login_ids"]:
                login_id = self._normalize(raw_login_id)
                if login_id not in login_ids:
                    login_ids.append(login_id)

            valid = []
            user_policy = UserPolicy()

            enrollments = None
            if len(login_ids) > 10:
                enrollments = Enrollments().get_enrollments_for_course(course_id)

            for login in login_ids:
                try:
                    name = ''
                    status = 'valid'
                    comment = 'Will add'
                    user_policy.valid(login)

                    if '@' not in login:
                        name = user_policy.get_person_by_netid(login).display_name

                    if enrollments:
                        for e in enrollments:
                            if e.login_id == login:
                                status = 'present'
                                comment = 'Already in course'
                    else:
                        try:
                            reg_id = login
                            if '@' not in login:
                                reg_id = CanvasUser.objects.get(net_id=login).reg_id

                                for course in Courses().get_courses_for_regid(reg_id):
                                    if course.course_id == course_id:
                                        status = 'present'
                                        comment = 'Already in course'
                        except CanvasUser.DoesNotExist:
                            pass

                except UserPolicyException as ex:
                    status = 'invalid'
                    comment = "%s" % ex

                valid.append({
                    'login': login,
                    'name': name,
                    'status': status,
                    'comment': comment
                })
                    
            return self.json_response({'users': valid})
        except Exception as ex:
            return self.error_response(400, message="Validation Error %s" % ex)

    def _normalize(self, login):
        uw_domains = ['uw.edu', 'washington.edu',
                      'u.washington.edu', 'cac.washington.edu',
                      'deskmail.washington.edu']
        match = re.match(r'^(.*)@(%s)$' % '|'.join(uw_domains), login)
        return match.group(1) if match else login


class CanvasCourseSections(RESTDispatch):
    """ Performs actions on Canvas Course Sections
        GET returns 200 with course sections.
    """
    def GET(self, request, **kwargs):
        sections = []
        course_id = kwargs['canvas_course_id']

        for s in Sections().get_sections_in_course(course_id):
            sections.append({
                'id': s.section_id,
                'name': s.name
            })

        return self.json_response({'sections': sorted(sections, key=lambda k: k['name'])})
