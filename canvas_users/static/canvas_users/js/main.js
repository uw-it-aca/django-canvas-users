/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars, top */
(function ($) {
    "use strict";
    $(document).ready(function () {

        // prep for api post/put
        function csrfSafeMethod(method) {
            // these HTTP methods do not require CSRF protection
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }

        $.ajaxSetup({
            crossDomain: false, // obviates need for sameOrigin test
            beforeSend: function (xhr, settings) {
                if (window.canvas_users.session_id) {
                    xhr.setRequestHeader("X-SessionId", window.canavs_users.session_id);
                }
                if (!csrfSafeMethod(settings.type)) {
                    xhr.setRequestHeader("X-CSRFToken", window.canvas_users.csrftoken);
                }
            }
        });

        function randomId(len) {
            var id = [];

            for (var i = 0; i < len; i++) {
                id.push("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[((Math.random() * 10000) % 36) | 0]);
            }

            return id.join('');
        }

        function problemAddingUsers(msg, add_container) {
            var tpl = Handlebars.compile($('#failure-tmpl').html()),
                modal_id = randomId(32),
                modal_container,
                error_msg;

            error_msg = 'PROBLEM PROBLEM';

            $('body').append(tpl({
                modal_id: modal_id,
                error_message: 'THIS IS  PROBLEM'
            }));

            modal_container = $('#' + modal_id);
            modal_container.modal({
                backdrop: 'static',
                show: true
            });

            modal_container.find('#start-over').on('click', function () {
                modal_container.modal('hide');
                add_container.modal('show');
                add_container.find('input, button, select, textarea').removeProp('disabled');
            });

            modal_container.on('hidden.bs.modal', function () {
                modal_container.remove();
            });
        };

        function importUsers(e) {
            var course_id = window.canvas_users.canvas_course_id,
                context = e.data.valid_context,
                valid_container = e.data.valid_container,
                add_container = e.data.add_container,
                logins = [];

            e.stopPropagation();

            valid_container.find('button').prop('disabled', true);

            $.each(context.users, function () {
                if (this.add) {
                    logins.push({
                        login: this.login,
                        regid: this.regid
                    });
                }
            });

            $.ajax({
                type: 'POST',
                url: 'api/v1/canvas/course/' + course_id + '/import',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({logins: logins})
            })
                .done(function (data) {
                    var progress = valid_container.find('.progress-overlay');

                    progress.height(valid_container.find('.modal-content').height());
                    progress.width(valid_container.find('.modal-content').width());
                    progress.removeClass('hidden');

                    (function () {
                        var interval_id = setInterval(function () {
                            $.ajax({
                                type: 'GET',
                                url: 'api/v1/canvas/course/' + course_id
                                    + '/import?import_id=' + data.import.id
                            })
                                .done(function (data) {
                                    if (parseInt(data.progress) >= 100) {
                                        clearInterval(interval_id);
                                        valid_container.modal('hide');
                                        add_container.remove();
                                    } else {
                                        valid_container.find('.progress-bar').css('width', data.progress + '%');
                                        valid_container.find('.progress-bar').html(data.progress + '%');
                                    }
                                })
                                .fail(function (msg) {
                                    clearInterval(interval_id);
                                    valid_container.modal('hide');
                                    problemAddingUsers(msg, add_container);
                                });
                        },
                        500);
                    })();
                })
                .fail(function (msg) {
                    valid_container.modal('hide');
                    problemAddingUsers(msg, add_container);
                });
        };

        function validateUsers(e) {
            var add_container = e.data.add_container,
                raw_users = add_container.find('#users-to-add').val().trim(),
                users_to_add = raw_users.split(/[ ,\n]+/),
                add_as_role_option = add_container.find('#added-users-role option:selected'),
                add_to_section_option = add_container.find('#added-users-section option:selected'),
                course_id = window.canvas_users.canvas_course_id,
                errors = false;

            e.stopPropagation();

            // validae form
            if (raw_users.length === 0 || users_to_add.length < 1) {
                $('#users-to-add').closest('.form-group').addClass('has-error');
                errors = true;
            }

            if (parseInt(add_as_role_option.val()) < 0) {
                add_as_role_option.closest('.form-group').addClass('has-error');
                errors = true;
            }

            if (parseInt(add_to_section_option.val()) < 0) {
                add_to_section_option.closest('.form-group').addClass('has-error');
                errors = true;
            }

            if (errors) {
                return;
            }

            add_container.find('input, button, select, textarea').prop('disabled', true);

            $.ajax({
                type: 'POST',
                url: 'api/v1/canvas/course/' + course_id + '/validate',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    login_ids: users_to_add,
                    role: add_as_role_option.text(),
                    section_name: add_to_section_option.text(),
                    section_id: add_to_section_option.val()
                })
            })
                .done(function (data) {
                    var tpl = Handlebars.compile($('#validated-users-tmpl').html()),
                        modal_id = randomId(32),
                        modal_container,
                        valid_context,
                        validated_users = [],
                        validated_user_count = 0;

                    $.each(data.users, function () {
                        if (this.status == 'valid') {
                            validated_user_count++;
                        }

                        validated_users.push({
                            add: (this.status == 'valid'),
                            present: (this.status == 'present'),
                            invalid: (this.status == 'invalid'),
                            login: this.login,
                            regid: this.regid,
                            name: this.name,
                            comment: this.comment
                        });
                    });

                    valid_context = {
                        modal_id: modal_id,
                        count: validated_user_count,
                        plural: (validated_user_count > 1) ? 's' : '',
                        exceptions: (validated_user_count != data.users.length),
                        total: data.users.length,
                        users: validated_users,
                        role: add_as_role_option.text(),
                        section_name: add_to_section_option.text(),
                        section_id: add_to_section_option.val()
                    };

                    $('body').append(tpl(valid_context));

                    add_container.modal('hide');

                    modal_container = $('#' + modal_id);
                    modal_container.modal({
                        backdrop: 'static',
                        show: true
                    });

                    modal_container.find('#validate-users').on('click', {
                        valid_container: modal_container,
                        add_container: add_container,
                        valid_context: valid_context
                    }, importUsers);
                    modal_container.find('#start-over').on('click', function () {
                        modal_container.modal('hide');
                        add_container.modal('show');
                        add_container.find('input, button, select, textarea').removeProp('disabled');
                    });

                    modal_container.on('hidden.bs.modal', function () {
                        modal_container.remove();
                    });
                })
                .fail(function (msg) {
                    modal_container.modal('hide');
                    problemAddingUsers(msg, add_container);
                });
        }

        function loadCourseRoles(account_id, container) {
            $.ajax({
                type: 'GET',
                url: 'api/v1/canvas/account/' + account_id + '/course/roles'
            })
                .done(function (data) {
                    var tpl = Handlebars.compile($('#input-users-role-tmpl').html()),
                        select = container.find('#added-users-role');

                    select.removeProp('disabled');
                    select.prev('.loading').addClass('hidden');
                    select.html(tpl({
                        roles: data.roles
                    }));
                });
        };

        function loadCourseSections(course_id, container) {
            $.ajax({
                type: 'GET',
                url: 'api/v1/canvas/course/' + course_id + '/sections'
            })
                .done(function (data) {
                    var tpl = Handlebars.compile($('#input-users-sections-tmpl').html()),
                        select = container.find('#added-users-section');

                    select.removeProp('disabled');
                    select.prev('.loading').addClass('hidden');
                    select.html(tpl({
                        sections: data.sections
                    }));
                });
        };
        
        function launchAddUsers() {
            var tpl = Handlebars.compile($('#input-users-tmpl').html()),
                container_id = randomId(32),
                account_id = window.canvas_users.canvas_account_id,
                course_id = window.canvas_users.canvas_course_id,
                modal_container;

            $('body').append(tpl({
                modal_id: container_id
            }));

            modal_container = $('#' + container_id);
            modal_container.modal({
                backdrop: 'static',
                show: true
            });

            modal_container.find('#validate-users').on('click',
                                                       {
                                                           add_container: modal_container
                                                       },
                                                       validateUsers);
            modal_container.delegate('input, textarea, select', 'focus',
                                      function (e) {
                                          $(e.target).closest('.form-group').removeClass('has-error');
                                      });

            loadCourseRoles(account_id, modal_container);
            loadCourseSections(course_id, modal_container);
        };

        launchAddUsers();

    });
}(jQuery));
