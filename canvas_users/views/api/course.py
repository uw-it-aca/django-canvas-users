from logging import getLogger
from django.db import connection
from uw_canvas.models import CanvasUser, CanvasSection, CanvasRole
from restclients_core.exceptions import DataFailureException
from sis_provisioner.models import CourseMember, Enrollment
from sis_provisioner.dao.canvas import get_user_by_sis_id, create_user
from canvas_users.dao.canvas import enroll_course_user
from canvas_users.views.api.rest_dispatch import UserRESTDispatch
from canvas_users.models import AddUser, AddUsersImport
from multiprocessing import Process
import json
import sys
import os


class ValidCanvasCourseUsers(UserRESTDispatch):
    """ Exposes API to manage Canvas users
        GET returns 200 with user details
    """
    def POST(self, request, **kwargs):
        try:
            blti_data = self.get_session(request)
            course_id = kwargs['canvas_course_id']
            data = json.loads(request.body)

            course_users = AddUser.objects.users_in_course(
                course_id, data['section_id'], data['role_base'],
                data['login_ids'])

            return self.json_response({
                'users': map(lambda u: u.json_data(), course_users)})

        except Exception as ex:
            return self.error_response(400, message="Validation Error %s" % ex)


class ImportCanvasCourseUsers(UserRESTDispatch):
    """ Exposes API to manage Canvas users
    """
    def __init__(self):
        self._log = getLogger(__name__)

    def GET(self, request, **kwargs):
        course_id = kwargs['canvas_course_id']
        try:
            import_id = request.GET['import_id']
            imp = AddUsersImport.objects.get(id=import_id)

            if imp.import_error:
                try:
                    msg = json.loads(imp.import_error)
                except Exception:
                    msg = imp.import_error
                return self.json_response({'error': msg}, status=400)

            if imp.progress() == 100:
                imp.delete()

            return self.json_response(imp.json_data())
        except AddUsersImport.DoesNotExist:
            return self.error_response(400, message="Unknown import id")
        except KeyError:
            return self.error_response(400, message="Missing import id")

    def POST(self, request, **kwargs):
        try:
            course_id = kwargs['canvas_course_id']
            data = json.loads(request.body)
            blti_data = self.get_session(request)
            importer = blti_data.get('custom_canvas_user_login_id')
            importer_id = blti_data.get('custom_canvas_user_id')
            users = AddUser.objects.users_in_course(
                course_id, data['section_id'], data['role_base'],
                [x['login'] for x in data['logins']])
            role = CanvasRole(
                role_id=data['role_id'],
                label=data['role'],
                base_role_type=data['role_base'])
            section = CanvasSection(
                section_id=data['section_id'],
                sis_section_id=data['section_sis_id'],
                course_id=course_id)
            section_only = data['section_only']
            notify_users = data['notify_users']
            imp = AddUsersImport(
                importer=importer,
                importer_id=importer_id,
                importing=len(users),
                course_id=course_id,
                role=role.label,
                section_id=section.sis_section_id)
            imp.save()

            connection.close()
            p = Process(target=self._api_import_users,
                        args=(imp.pk, users, role, section,
                              section_only, notify_users))
            p.start()

            return self.json_response(imp.json_data())
        except KeyError as ex:
            return self.error_response(
                400, message="Incomplete Request: %s" % ex)
        except Exception as ex:
            return self.error_response(
                400, message="Import Error: %s" % ex)

    def _api_import_users(self, import_id, users, role,
                          section, section_only, notify_users):
        try:
            imp = AddUsersImport.objects.get(id=import_id)
            imp.import_pid = os.getpid()
            imp.save()

            for u in users:
                try:
                    canvas_user = get_user_by_sis_id(u.regid)
                except DataFailureException as ex:
                    if ex.status == 404:
                        self._log.info(
                            'CREATE USER "%s" login: %s reg_id: %s' % (
                                u.name, u.login, u.regid))

                        # add user as "admin" on behalf of importer
                        canvas_user = create_user(CanvasUser(
                            name=u.name,
                            login_id=u.login,
                            sis_user_id=u.regid,
                            email=u.email))
                    else:
                        raise Exception(
                            'Cannot create user %s: %s' % (u.login, ex))

                self._log.info(
                    '%s ADDING %s (%s) TO %s: %s '
                    '(%s) AS %s (%s) - O:%s, N:%s' % (
                        imp.importer, canvas_user.login_id,
                        canvas_user.user_id, section.course_id,
                        section.sis_section_id, section.section_id, role.label,
                        role.role_id, section_only, notify_users))

                enroll_course_user(
                    as_user=imp.importer_id,
                    course_id=section.course_id,
                    section_id=section.section_id,
                    user_id=canvas_user.user_id,
                    role_type=role.base_role_type,
                    role_id=role.role_id,
                    section_only=section_only,
                    notify_users=notify_users)

                imp.imported += 1
                imp.save()

        except DataFailureException as ex:
            self._log.info('EXCEPTION: %s' % (ex))
            try:
                msg = json.loads(ex.msg)
                imp.import_error = json.dumps({
                    'url': ex.url, 'status': ex.status, 'msg': msg})
            except Exception:
                imp.import_error = "%s" % (ex)
            imp.save()

        except Exception as ex:
            self._log.info('EXCEPTION: %s' % (ex))
            imp.import_error = "%s" % (ex)
            imp.save()

        sys.exit(0)
