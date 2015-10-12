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
                    regid = ''
                    user_policy.valid(login)

                    if '@' not in login:
                        person = user_policy.get_person_by_netid(login)
                        name = person.display_name
                        regid = person.uwregid

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
                    'regid': regid,
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


class ImportCanvasCourseUsers(RESTDispatch):
    """ Exposes API to manage Canvas users 
        GET returns 200 with user details
    """
    def GET(self, request, **kwargs):
        sections = []
        course_id = kwargs['canvas_course_id']
        try:
            import_id = request.GET['import_id']

            import random
            n = (random.random() * 10000) % 100

            if n > 82:
                progress = 100
            else:
                progress = (random.random() * 10000) % 100



            return self.json_response({'progress': int(progress)})
        except KeyError:
            return self.error_response(400, message="Missing import_id")

    def POST(self, request, **kwargs):
        try:
            course_id = kwargs['canvas_course_id']
            data = json.loads(request.body)

            from time import sleep
            sleep(1.25)

            import random
            if ((random.random() * 10000) % 100) > 80:
                return self.error_response(400, message="FAILED IMPORT")


#            for login in data['login_ids']:
#                try:
#                except UserPolicyException as ex:
#                    raise Exception('Invalid User: %s' % ex)

            return self.json_response({'import': {'id': '123456'}})
        except Exception as ex:
            return self.error_response(400, message="Import Error %s" % ex)


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
