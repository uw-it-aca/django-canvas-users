# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from logging import getLogger
from django.db import connection
from uw_canvas.models import CanvasSection, CanvasRole
from restclients_core.exceptions import DataFailureException
from canvas_users.dao.canvas import (
    get_user_by_sis_id, create_user, enroll_course_user)
from canvas_users.views import UserRESTDispatch
from canvas_users.models import AddUser, AddUsersImport
from multiprocessing import Process
import json
import sys
import os

logger = getLogger(__name__)


class ValidCanvasCourseUsers(UserRESTDispatch):
    """ Exposes API to manage Canvas users
        GET returns 200 with user details
    """
    def post(self, request, *args, **kwargs):
        try:
            course_id = kwargs['canvas_course_id']
            data = json.loads(request.body)

            course_users = AddUser.objects.users_in_course(
                course_id, data['section_id'], data['role_base'],
                data['login_ids'])

            return self.json_response({
                'users': [user.json_data() for user in course_users]
            })

        except Exception as ex:
            return self.error_response(
                400, message='Validation Error {}'.format(ex))


class ImportCanvasCourseUsers(UserRESTDispatch):
    """ Exposes API to manage Canvas users
    """
    def get(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
        try:
            course_id = kwargs['canvas_course_id']
            data = json.loads(request.body)
            logins = [x['login'] for x in data['logins']]

            users = []
            for user in AddUser.objects.users_in_course(
                    course_id, data['section_id'], data['role_base'], logins):
                if user.is_valid():
                    users.append(user)

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
                importer=self.blti.user_login_id,
                importer_id=self.blti.canvas_user_id,
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
                400, message='Incomplete Request: {}'.format(ex))
        except Exception as ex:
            return self.error_response(
                400, message='Import Error: {}'.format(ex))

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
                        logger.info(
                            'CREATE USER "{}", login: {}, reg_id: {}'.format(
                                u.name, u.login, u.regid))

                        # add user as "admin" on behalf of importer
                        canvas_user = create_user(
                            name=u.name,
                            login_id=u.login,
                            sis_user_id=u.regid,
                            email=u.email)
                    else:
                        raise Exception('Cannot create user {}: {}'.format(
                            u.login, ex))

                logger.info(
                    '{importer} ADDING {user} ({user_id}) TO {course_id}: '
                    '{sis_section_id} ({section_id}) AS {role} ({role_id}) '
                    '- O:{section_only}, N:{notify}'.format(
                        importer=imp.importer, user=canvas_user.login_id,
                        user_id=canvas_user.user_id,
                        course_id=section.course_id,
                        sis_section_id=section.sis_section_id,
                        section_id=section.section_id, role=role.label,
                        role_id=role.role_id, section_only=section_only,
                        notify=notify_users))

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
            logger.info('Request failed: {}'.format(ex))
            try:
                msg = json.loads(ex.msg)
                imp.import_error = json.dumps({
                    'url': ex.url, 'status': ex.status, 'msg': msg})
            except Exception:
                imp.import_error = '{}'.format(ex)
            imp.save()

        except Exception as ex:
            logger.info('EXCEPTION: {}'.format(ex))
            imp.import_error = '{}'.format(ex)
            imp.save()

        sys.exit(0)
