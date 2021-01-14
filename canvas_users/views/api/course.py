from canvas_users.views import UserRESTDispatch
from canvas_users.models import AddUser, AddUsersImport
import json


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
            return self.error_response(404, message="Unknown import id")
        except KeyError:
            return self.error_response(400, message="Missing import id")

    def post(self, request, *args, **kwargs):
        try:
            course_id = kwargs['canvas_course_id']

            data = json.loads(request.body)
            section_id = data['section_id']
            sis_section_id = data['section_sis_id']
            role_base = data['role_base']
            role_id = data['role_id']
            role_label = data['role']
            section_only = data['section_only']
            notify_users = data['notify_users']

            users = AddUser.objects.users_in_course(
                course_id, section_id, role_base,
                [x['login'] for x in data.get('logins', [])])

            imp = AddUsersImport(
                importer=self.blti.user_login_id,
                importer_id=self.blti.canvas_user_id,
                importing=len(users),
                course_id=course_id,
                role=role_label,
                role_id=role_id,
                role_base=role_base,
                section_id=sis_section_id,
                section_only=section_only,
                notify_users=notify_users)
            imp.save()

            for user in users:
                user.importjob = imp
                user.save()

            imp.start()

            return self.json_response(imp.json_data())
        except KeyError as ex:
            return self.error_response(
                400, message='Incomplete Request: {}'.format(ex))
        except Exception as ex:
            return self.error_response(
                400, message='Import Error: {}'.format(ex))
