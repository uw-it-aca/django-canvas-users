from django.conf import settings
from blti.views.rest_dispatch import RESTDispatch
from sis_provisioner.models import User as CanvasUser, Import
from sis_provisioner.models import PRIORITY_DEFAULT
from restclients.canvas.sections import Sections
from restclients.canvas.courses import Courses
from restclients.canvas.enrollments import Enrollments
from restclients.exceptions import DataFailureException
from sis_provisioner.csv_builder import CSVBuilder
from sis_provisioner.policy import UserPolicy, UserPolicyException
from sis_provisioner.models import CourseMember, Enrollment, \
    MissingImportPathException
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

            if not login_ids:
                return self.json_response({'users': []})

            valid = []
            user_policy = UserPolicy()
            enrollments = Enrollments()
            for login in login_ids:
                try:
                    name = ''
                    status = 'valid'
                    comment = 'Prepared to add'
                    regid = ''
                    user_policy.valid(login)

                    if '@' in login:
                        canvas_user = user_policy.get_person_by_gmail_id(login)
                        regid = canvas_user.sis_user_id
                    else:
                        person = user_policy.get_person_by_netid(login)
                        name = person.display_name
                        regid = person.uwregid

                    for e in enrollments.search_enrollments_for_course(course_id, login):
                        if e.login_id == login:
                            status = 'present'
                            comment = 'Already in course'
                            break

                except DataFailureException as ex:
                    if ex.status != 401:
                        raise
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
        course_id = kwargs['canvas_course_id']
        try:
            import_id = request.GET['import_id']
            imp = Import.objects.get(id=import_id)

            if not imp.canvas_id:
                return self.error_response(400, message="Missing Canvas Id")

            imp.update_import_status()
            imp = Import.objects.get(id=import_id)
            if imp.is_imported():
                return self.json_response({'progress': 100})
            elif imp.monitor_status != 200 or imp.canvas_errors:
                return self.error_response(
                    400, message="Import Canvas error (%s): %s" % (
                        imp.monitor_status, imp.canvas_errors))

            return self.json_response({'progress': imp.canvas_progress})
        except Import.DoesNotExist:
            return self.json_response({'progress': 100})
        except KeyError:
            return self.error_response(400, message="Missing import_id")

    def POST(self, request, **kwargs):
        try:
            course_id = kwargs['canvas_course_id']
            data = json.loads(request.body)

            # use group (enroll user in section) csv plumbing.
            import_id = None
            csv_builder = CSVBuilder()
            role = data['role']
            course_sis_id = data['course_sis_id']
            section_id = data['section_id']
            section_sis_id = data['section_sis_id']

            if not (section_sis_id and len(section_sis_id) > 0):
                raise Exception('need to apply sis_id %s' % ('section_%s' % section_id))

            members = []
            for login in data['logins']:
                members.append(CourseMember(name=login['login'],
                                            course_id=course_sis_id,
                                            role=role,is_deleted=None,
                                            member_type=CourseMember.EPPN_TYPE \
                                                if '@' in login['login'] else \
                                                CourseMember.UWNETID_TYPE))

            for member in members:
                csv_builder.generate_csv_for_groupmember(member, section_sis_id,
                                                 member.role,
                                                 status=Enrollment.ACTIVE_STATUS)

            path = csv_builder._csv.write_files()
            if not path:
                return self.error_response(400, message="No CSV Path")

            imp = Import(priority=PRIORITY_DEFAULT,
                         csv_path=path,
                         csv_type='enrollment')
            imp.save()

            try:
                imp.import_csv()
                return self.json_response({'import': {'id': imp.pk}})
            except MissingImportPathException as ex:
                error_msg = "Import CSV Error: %s" % (imp.csv_errors if imp.csv_errors else ex)
                imp.delete()
                return self.error_response(400, message=error_msg)

        except Exception as ex:
            return self.error_response(400, message="Import Error: %s" % ex)


class CanvasCourseSections(RESTDispatch):
    """ Performs actions on Canvas Course Sections
        GET returns 200 with course sections.
    """
    def GET(self, request, **kwargs):
        sections = []
        course_id = kwargs['canvas_course_id']

        for s in Sections().get_sections_in_course(course_id):
            if not re.match(r'.*-groups$', s.sis_section_id):
                sections.append({
                    'id': s.section_id,
                    'sis_id': s.sis_section_id,
                    'name': s.name
                })

        return self.json_response({'sections': sorted(sections, key=lambda k: k['name'])})
