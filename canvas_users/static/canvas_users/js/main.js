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

        function validateUsers(e) {
            var add_container = $('#' + window.canvas_users.add_id),
                raw_users = add_container.find('#users-to-add').val().trim(),
                users_to_add = raw_users.split(/[ ,\n]+/),
                add_as_role = add_container.find('#added-users-role option:selected'),
                add_to_section = add_container.find('#added-users-section option:selected'),
                course_id = window.canvas_users.canvas_course_id,
                errors = false;

            e.stopPropagation();

            if (raw_users.length === 0 || users_to_add.length < 1) {
                $('#users-to-add').closest('.form-group').addClass('has-error');
                errors = true;
            }

            if (parseInt(add_as_role.val()) < 0) {
                add_as_role.closest('.form-group').addClass('has-error');
                errors = true;
            }

            if (parseInt(add_to_section.val()) < 0) {
                add_to_section.closest('.form-group').addClass('has-error');
                errors = true;
            }

            if (!errors) {
                launchUserValidation(course_id, {
                    login_ids: users_to_add,
                    role: add_as_role.text(),
                    section_name: add_to_section.text(),
                    section_id: add_to_section.val()
                });
            }
        };

        function launchUserValidation(course_id, users) {
            var tpl = Handlebars.compile($('#validated-users-tmpl').html()),
                add_container = $('#' + window.canvas_users.add_id);

            add_container.find('input, button, select, textarea').prop('disabled', true);

            $.ajax({
                type: 'POST',
                url: 'api/v1/canvas/course/' + course_id + '/validate',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(users)
            })
                .done(function (data) {
                    var modal_id = randomId(32),
                        modal_container,
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
                            name: this.name,
                            comment: this.comment
                        });
                    });

                    $('body').append(tpl({
                        modal_id: modal_id,
                        count: validated_user_count,
                        exceptions: (validated_user_count != data.users.length),
                        total: data.users.length,
                        users: validated_users,
                        role: users.role,
                        section_name: users.section_name,
                        section_id: users.section_id
                    }));

                    add_container.modal('hide');

                    modal_container = $('#' + modal_id);
                    modal_container.modal({
                        backdrop: 'static',
                        show: true
                    });

                    modal_container.find('#validate-users').on('click', validateUsers);
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
                    alert('DAMMIT');
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

            window.canvas_users.add_id = container_id;

            $('body').append(tpl({
                modal_id: container_id
            }));

            modal_container = $('#' + container_id);
            modal_container.modal({
                backdrop: 'static',
                show: true
            });

            modal_container.find('#validate-users').on('click', validateUsers);
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
