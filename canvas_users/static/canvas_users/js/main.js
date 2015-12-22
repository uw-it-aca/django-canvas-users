/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars, top */
(function ($) {
    "use strict";
    $(document).ready(function () {

        var ferpa_base_roles = ['TeacherEnrollment', 'TaEnrollment'];

        // prep for api post/put
        function csrfSafeMethod(method) {
            // these HTTP methods do not require CSRF protection
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }

        $.ajaxSetup({
            crossDomain: false, // obviates need for sameOrigin test
            beforeSend: function (xhr, settings) {
                if (window.canvas_users.session_id) {
                    xhr.setRequestHeader("X-SessionId", window.canvas_users.session_id);
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

        function setProgress(container, progress) {
            container.find('.progress-bar').css('width', progress + '%')
                .attr('aria-valuenow', progress)
                .html(progress + '%');
        };

        function confirmFERPA(e) {
            var tpl = Handlebars.compile($('#ferpa-tmpl').html()),
                modal_id = randomId(32),
                modal_container,
                error_msg,
                $confirmation,
                e_data = e.data;

            $('body').append(tpl({
                modal_id: modal_id,
            }));

            modal_container = $('#' + modal_id);
            modal_container.modal({
                backdrop: 'static',
                show: true
            });

            $confirmation = modal_container.find('button.confirmation');
            $confirmation.on('click', function (e) {
                modal_container.modal('hide');
                e.data = e_data;
                importUsers(e);
            });

            modal_container.find('#confirmed').on('change', function () {
                if ($(this).is(':checked')) {
                    $confirmation.removeProp('disabled');
                } else {
                    $confirmation.prop('disabled', true);
                }
            });

            modal_container.on('hidden.bs.modal', function () {
                modal_container.remove();
            });
        };

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

            if (add_container) {
                modal_container.find('button.start-over').on('click', function () {
                    modal_container.modal('hide');
                    add_container.modal('show');
                    add_container.find('button').removeClass('working');
                    add_container.find('input, button, select, textarea').removeProp('disabled');
                });
            } else {
                modal_container.find('.start-over').hide();
            }

            modal_container.on('hidden.bs.modal', function () {
                modal_container.remove();
            });
        };

        function timeoutAddingUsers() {
            var tpl = Handlebars.compile($('#timed-out-tmpl').html()),
                modal_id = randomId(32),
                modal_container,
                error_msg;

            $('body').append(tpl({
                modal_id: modal_id
            }));

            modal_container = $('#' + modal_id);
            modal_container.modal({
                backdrop: 'static',
                show: true
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
                logins = [],
                progress;

            e.stopPropagation();

            valid_container.find('button').prop('disabled', true);

            progress = valid_container.find('.progress-overlay');
            progress.height(valid_container.find('.modal-content').height());
            progress.width(valid_container.find('.modal-content').width());
            progress.removeClass('hidden');

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
                data: JSON.stringify({
                    logins: logins,
                    role: context.role,
                    course_id: window.canvas_users.canvas_course_id,
                    course_sis_id: window.canvas_users.sis_course_id,
                    section_id: context.section_id,
                    section_sis_id: context.section_sis_id
                })
            })
                .done(function (data) {
                    var nth = Math.floor(75 / logins.length),
                        initial_percent = nth + Math.floor((Math.random() * 15) + 5);

                    setProgress(valid_container, initial_percent);

                    if (data.import.id === null) {
                        valid_container.modal('hide');
                        add_container.remove();
                    } else {
                        (function () {
                            var times = 0,
                                interval_id = setInterval(function () {
                                    times += 1;

                                    if (times > 60) {
                                        clearInterval(interval_id);
                                        valid_container.modal('hide');
                                        add_container.remove();
                                        timeoutAddingUsers();
                                    }

                                    $.ajax({
                                        type: 'GET',
                                        url: 'api/v1/canvas/course/' + course_id
                                            + '/import?import_id=' + data.import.id
                                    })
                                        .done(function (data) {
                                            if (data.progress == null || parseInt(data.progress) >= 100) {
                                                clearInterval(interval_id);
                                                valid_container.modal('hide');
                                                add_container.remove();
                                                finishAddUsers();
                                            } else if (parseInt(data.progress) > initial_percent) {
                                                setProgress(valid_container, data.progress);
                                            }
                                        })
                                        .fail(function (msg) {
                                            clearInterval(interval_id);
                                            valid_container.modal('hide');
                                            problemAddingUsers(msg, add_container);
                                        });
                                },
                                1000);
                        })();
                    }
                })
                .fail(function (msg) {
                    valid_container.modal('hide');
                    problemAddingUsers(msg, add_container);
                });
        };

        function validatableUsers(e) {
            var $this = $(this), 
                $dialog = $this.closest('.modal-dialog'),
                $button = $dialog.find('#validate-users');

            if ($dialog.find('#users-to-add').val().trim().length
                && $dialog.find('#added-users-role option:selected').val().length
                && $dialog.find('#added-users-section option:selected').val().length) {
                $button.removeProp('disabled');
            } else {
                $button.prop('disabled', true);
            }
        }

        function validateUsers(e) {
            var add_container = e.data.add_container,
                raw_users = add_container.find('#users-to-add').val().trim(),
                users_to_add = raw_users.split(/[ ,\n]+/),
                add_as_role_option = add_container.find('#added-users-role option:selected'),
                add_to_section_option = add_container.find('#added-users-section option:selected'),
                add_to_section_vals = add_to_section_option.val().split('|'),
                course_id = window.canvas_users.canvas_course_id,
                errors = false,
                role_value,
                is_ferpa_role = false;

            e.stopPropagation();

            // validate form
            if (raw_users.length === 0 || users_to_add.length < 1) {
                $('#users-to-add').closest('.form-group').addClass('has-error');
                errors = true;
            }

            role_value = add_as_role_option.val();
            if (role_value.length) {
                is_ferpa_role = (ferpa_base_roles.indexOf(role_value.split('|')[1]) >= 0);
            } else {
                add_as_role_option.closest('.form-group').addClass('has-error');
                errors = true;
            }

            if (add_to_section_vals.length !== 2) {
                add_to_section_option.closest('.form-group').addClass('has-error');
                errors = true;
            }

            if (errors) {
                return;
            }

            add_container.find('button').addClass('working');
            add_container.find('input, button, select, textarea').prop('disabled', true);

            $.ajax({
                type: 'POST',
                url: 'api/v1/canvas/course/' + course_id + '/validate',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    login_ids: users_to_add
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
                        no_logins: (validated_user_count < 1),
                        count_plural: (validated_user_count > 1) ? 's' : '',
                        total_plural: (data.users.length > 1) ? 's' : '',
                        exceptions: (validated_user_count != data.users.length),
                        total: data.users.length,
                        users: validated_users,
                        role: add_as_role_option.text(),
                        section_name: add_to_section_option.text(),
                        section_id: add_to_section_vals[0],
                        section_sis_id: add_to_section_vals[1]
                    };

                    $('body').append(tpl(valid_context));

                    add_container.modal('hide');

                    modal_container = $('#' + modal_id);
                    modal_container.modal({
                        backdrop: 'static',
                        show: true
                    });

                    if (validated_user_count < 1) {
                        modal_container.find('#validate-users').attr('data-dismiss', 'modal');
                    } else {
                        modal_container.find('#validate-users').on('click', {
                            valid_container: modal_container,
                            add_container: add_container,
                            valid_context: valid_context
                        }, (is_ferpa_role) ? confirmFERPA : importUsers);
                    }

                    modal_container.find('button.start-over').on('click', function () {
                        modal_container.modal('hide');
                        add_container.modal('show');
                        add_container.find('button').removeClass('working');
                        add_container.find('input, button, select, textarea').removeProp('disabled');
                    });

                    modal_container.delegate('button.close', 'click', finishAddUsers);
                    modal_container.on('hidden.bs.modal', function () {
                        modal_container.remove();
                    });
                })
                .fail(function (msg) {
                    add_container.modal('hide');
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

                    select.removeProp('disabled').removeClass('loading');
                    select.prev('.loading').addClass('hidden');
                    select.html(tpl({
                        plural: (data.roles.length > 1),
                        roles: data.roles
                    }));
                })
                .fail(function (msg) {
                    if (container.hasClass('in')) {
                        container.modal('hide');
                        problemAddingUsers(msg);
                    }
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

                    select.removeProp('disabled').removeClass('loading');
                    select.prev('.loading').addClass('hidden');
                    select.html(tpl({
                        plural: (data.sections.length > 1),
                        sections: data.sections
                    }));
                })
                .fail(function (msg) {
                    if (container.hasClass('in')) {
                        container.modal('hide');
                        problemAddingUsers(msg);
                    }
                });
        };

        function finishAddUsers(e) {
            var canvas_host = window.canvas_users.canvas_host,
                course_id = window.canvas_users.canvas_course_id;

            top.location = 'https://' + canvas_host + '/courses/' + course_id + '/users';
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

            modal_container.find('#users-to-add').on('keyup', validatableUsers);
            modal_container.find('select').on('change', validatableUsers);
            modal_container.delegate('button.close', 'click', finishAddUsers);

            loadCourseRoles(account_id, modal_container);
            loadCourseSections(course_id, modal_container);
        };

        launchAddUsers();
    });
}(jQuery));
