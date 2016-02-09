/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars, top */


(function ($) {
    "use strict";
    $(document).ready(function () {

        var ferpa_base_roles = ['TeacherEnrollment', 'TaEnrollment', 'DesignerEnrollment'];

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
                if (window.canvas_users.hasOwnProperty('csrftoken')
                    && window.canvas_users.csrftoken
                    && !csrfSafeMethod(settings.type)) {
                    xhr.setRequestHeader("X-CSRFToken", window.canvas_users.csrftoken);
                }
            }
        });

        function getModal(e) {
            return $(e.target).closest('.ReactModal__Content');
        }

        function hideModalPanels($modal) {
            $modal.find('.uw-add-people-gather, .uw-add-people-confirm,'
                        + '.uw-add-people-ferpa, .uw-add-people-problem,'
                        + '.uw-add-people-timedout,').hide();
        }

        function showPeopleGather($modal) {
            hideModalPanels($modal);
            $modal.find('.uw-add-people-gather').show();
            validateGatherForm($modal);
            $modal.find('#uw-users-to-add').focus();
        }

        function showPeopleConfirmation($modal) {
            hideModalPanels($modal);
            $modal.find('.uw-add-people-confirm,').show();
            $modal.find('#uw-add-people-import').focus();
        }

        function showPeopleFERPA($modal) {
            var $ferpa = $modal.find('.uw-add-people-ferpa');

            hideModalPanels($modal);
            $ferpa.show();
            $ferpa.find('#confirmed').focus();
        }

        function showPeopleTimedOut($modal) {
            hideModalPanels($modal);
            $modal.find('.uw-add-people-timedout').show();
        }

        function showPeopleProblem($modal) {
            hideModalPanels($modal);
            $modal.find('.uw-add-people-problem').show();
        }

        function startOver(e) {
            var $modal = getModal(e);

            e.stopPropagation();
            showPeopleGather($modal);
        }

        function confirmFERPA(e) {
            var $modal = getModal(e),
                role = $modal.find('.uw-add-people-validation-result form input').val();

            e.stopPropagation();
            e.preventDefault();
            if (ferpa_base_roles.indexOf(role) >= 0) {
                $modal.find('div.uw-add-people-ferpa #confirmed').prop('checked', false);
                $modal.find('button#uw-add-people-ferpa-confirm').prop('disabled', true);
                showPeopleFERPA($modal);
            } else {
                importUsers(e);
            }
        };

        function problemAddingUsers(msg, $modal) {
            var tpl = Handlebars.templates['failure_modal'];

            $modal.find('div.uw-add-people-problem').html(tpl({
                error_message: 'PROBLEM IS ' + (msg ? msg : 'unspecified')
            }));

            showPeopleProblem($modal);
        };

        function timeoutAddingUsers($modal) {
            showPeopleTimedOut($modal);
        };

        function canvasFlashMessage(type, message) {
            var $holder = $('#flash_message_holder'),
                $li = $('<li class="ic-flash-' + type + '"><i></i>'
                        + message
                        + '<a href="#" class="close_link icon-end">Close</a></li>');

            $li.appendTo($holder).
                css('z-index', 1).
                show({
                    duration: 'fast',
                    start: function () {
                        $(this).css('z-index', 2);
                    }
                }).
                delay(5000).
                animate({'z-index': 1}, 0).
                fadeOut('slow', function () {
                    $(this).slideUp('fast', function () {
                        $(this).remove();
                    });
                });
        }

        function importUsers(e) {
            var $modal = getModal(e),
                $modalbox = $modal.find('.ReactModal__Layout'),
                $progressbaroverlay = $modal.find('.uw-add-people-confirm .uw-add-people-progress-overlay'),
                $progressbar = $progressbaroverlay.find('#progressbar'),
                $progressbarlabel = $progressbaroverlay.find('#progressbar .progress-label'),
                context = window.canvas_users.validated_context,
                logins = [],
                progress;

            e.stopPropagation();
            e.preventDefault();

            showPeopleConfirmation($modal);

            $progressbaroverlay.show();
            $progressbar.progressbar({
                value: 3,
                change: function () {
                    $progressbarlabel.text($progressbar.progressbar('value') + '%');
                }
            });

            $progressbaroverlay.offset({
                top: $modalbox.offset().top,
                left: $modalbox.offset().left
            });
            $progressbaroverlay.css('height', $modalbox.height());
            $progressbaroverlay.css('width',$modalbox.width());

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
                url: 'https://'
                    + window.canvas_users.canvas_users_host
                    + '/users/api/v1/canvas/course/'
                    + window.canvas_users.canvas_course_id + '/import',
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
                    if (data.import.id === null) {
                        finishImport(logins.length, context.role, $modal);
                    } else {
                        monitorImport(data.import.id, logins.length, context.role, $modal);
                    }
                })
                .fail(function (msg) {
                    problemAddingUsers(msg, $modal);
                });
        }

        function monitorImport(import_id, user_count, role, $modal) {
            var $progressbar = $modal.find('.uw-add-people-progress-overlay #progressbar'),
                nth = Math.floor(75 / user_count),
                initial_percent = nth + Math.floor((Math.random() * 15) + 5),
                timeout_id,
                interval_id;

            $progressbar.progressbar('value', initial_percent);

            // we have 60 seconds to finish
            timeout_id = window.setTimeout(function () {
                $progressbar.trigger('uw-add-user.import-timeout');
            }, 60 * 1000);

            // poll once every second, but don't block
            interval_id = window.setInterval(function () {
                monitorImportProgress(import_id, $progressbar);
            }, 1000);

            $progressbar.off('uw-add-user.import-progress')
                .on('uw-add-user.import-progress', function (e, progress) {
                    if (progress > initial_percent) {
                        $progressbar.progressbar('value', progress);
                    }
                });

            $progressbar.off('uw-add-user.import-success')
                .on('uw-add-user.import-success', function () {
                    $progressbar.off('uw-add-user.import-success');
                    window.clearInterval(interval_id);
                    window.clearTimeout(timeout_id);
                    finishImport(user_count, role, $modal);
                });

            $progressbar.off('uw-add-user.import-fail')
                .on('uw-add-user.import-fail', function (e, msg) {
                    window.clearInterval(interval_id);
                    window.clearTimeout(timeout_id);
                    problemAddingUsers(msg, $modal);
                });

            $progressbar.off('uw-add-user.import-timeout')
                .on('uw-add-user.import-timeout', function () {
                    window.clearInterval(interval_id);
                    timeoutAddingUsers($modal);
                });
        }

        function monitorImportProgress(import_id, $progressbar) {
            $.ajax({
                type: 'GET',
                url: 'https://'
                    + window.canvas_users.canvas_users_host
                    + '/users/api/v1/canvas/course/'
                    + window.canvas_users.canvas_course_id
                    + '/import?import_id=' + import_id
            })
                .done(function (data) {
                    var progress = (data.progress) ? parseInt(data.progress) : 100;

                    if (progress >= 100) {
                        $progressbar.trigger('uw-add-user.import-success');
                    } else {
                        $progressbar.trigger('uw-add-user.import-progress',
                                             [ progress ]);
                    }
                })
                .fail(function (msg) {
                    $progressbar.trigger('uw-add-user.import-fail', [msg]);
                });
        }

        function finishImport(count, role, $modal) {
            finishAddPeopleModal($modal);
            canvasFlashMessage('success',
                               'Added ' + count + ' '
                               + role + ((count > 1) ? 's' : ''));
        }

        function validatableUsers(e) {
            validateGatherForm(getModal(e));
        }

        function validateGatherForm($modal) {
            var $button = $modal.find('button#uw-add-people-validate');

            if ($modal.find('#uw-users-to-add').val().trim().length
                && $modal.find('#uw-added-users-role option:selected').val().length
                && $modal.find('#uw-added-users-section option:selected').val().length) {
                $button.removeProp('disabled');
            } else {
                $button.prop('disabled', true);
            }
        }

        function validateUsers(e) {
            var $modal = getModal(e),
                raw_users = $modal.find('#uw-users-to-add').val().trim(),
                users_to_add = raw_users.split(/[ ,\n]+/),
                add_as_role_option = $modal.find('#uw-added-users-role option:selected'),
                add_as_role_vals = add_as_role_option.val().split('|'),
                add_to_section_option = $modal.find('#uw-added-users-section option:selected'),
                add_to_section_vals = add_to_section_option.val().split('|'),
                errors = false;

            e.stopPropagation();

            // validate form
            if (raw_users.length === 0 || users_to_add.length < 1) {
                $('#uw-users-to-add').closest('.ic-Form-control').addClass('ic-Form-control--has-error');
                errors = true;
            }

            if (add_as_role_vals.length !== 2) {
                add_as_role_option.closest('.ic-Form-control').addClass('ic-Form-control--has-error');
                errors = true;
            }

            if (add_to_section_vals.length !== 2) {
                add_to_section_option.closest('.ic-Form-control').addClass('ic-Form-control--has-error');
                errors = true;
            }

            if (errors) {
                return;
            }

            $modal.find('button#uw-add-people-validate').addClass('uw-add-people-loading').prop('disabled', true);
            $('.uw-add-people-gather', $modal).find('input, button, select, textarea').prop('disabled', true);

            $.ajax({
                type: 'POST',
                url: 'https://'
                    + window.canvas_users.canvas_users_host
                    + '/users/api/v1/canvas/course/'
                    + window.canvas_users.canvas_course_id
                    + '/validate',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    login_ids: users_to_add
                })
            })
                .done(function (data) {
                    var tpl = Handlebars.templates['validate_users'],
                        tpl_button = Handlebars.templates['add_users_button'],
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
                        count: validated_user_count,
                        no_logins: (validated_user_count < 1),
                        count_plural: (validated_user_count > 1) ? 's' : '',
                        total_plural: (data.users.length > 1) ? 's' : '',
                        exceptions: (validated_user_count != data.users.length),
                        total: data.users.length,
                        users: validated_users,
                        role: add_as_role_option.text(),
                        role_name: add_as_role_vals[1],
                        section_name: add_to_section_option.text(),
                        section_id: add_to_section_vals[0],
                        section_sis_id: add_to_section_vals[1]
                    };

                    window.canvas_users.validated_context = valid_context;

                    $modal.find('div.uw-add-people-confirm').html(tpl(valid_context));
                    $modal.find('button#uw-add-people-import').html(tpl_button({
                        count: validated_user_count,
                        plural: (validated_user_count === 1) ? '' : 's',
                        role: add_as_role_option.text()
                    }));

                    showPeopleConfirmation($modal);

                    if (validated_user_count === 0) {
                        $modal.find('button#uw-add-people-import').hide();
                        $modal.find('button.uw-add-people-close').show();
                    }
                })
                .fail(function (msg) {
                    problemAddingUsers(msg, $modal);
                })
                .always(function () {
                    $modal.find('.uw-add-people-loading').removeClass('uw-add-people-loading');
                    $('.uw-add-people-gather', $modal).find('input, button, select, textarea').removeProp('disabled');
                });
        }

        function loadCourseRoles(account_id, $modal) {
            var $select = $modal.find('#uw-added-users-role');

            $.ajax({
                type: 'GET',
                url: 'https://'
                    + window.canvas_users.canvas_users_host
                    + '/users/api/v1/canvas/account/' + account_id + '/course/roles',
                async: true
            })
                .done(function (data) {
                    var tpl = Handlebars.templates['add_users_role'];

                    $select.html(tpl({
                        plural: (data.roles.length > 1),
                        roles: data.roles
                    }));
                })
                .fail(function (msg) {
                    problemAddingUsers(msg, $modal);
                })
                .always(function () {
                    $select.removeProp('disabled').removeClass('uw-add-people-loading');
                });
        };

        function loadCourseSections(course_id, $modal) {
            var $select = $modal.find('#uw-added-users-section');

            $.ajax({
                type: 'GET',
                url: 'https://'
                    + window.canvas_users.canvas_users_host
                    + '/users/api/v1/canvas/course/' + course_id + '/sections',
                async: true
            })
                .done(function (data) {
                    var tpl = Handlebars.templates['add_users_section'];

                    $select.html(tpl({
                        plural: (data.sections.length > 1),
                        sections: data.sections
                    }));
                })
                .fail(function (msg) {
                    problemAddingUsers(msg, $modal);
                })
                .always(function () {
                    $select.removeProp('disabled').removeClass('uw-add-people-loading');
                });
        };

        function finishAddPeople(e) {
            finishAddPeopleModal(getModal(e));
        }

        function finishAddPeopleModal($modal) {
            var $gather = $modal.find('.uw-add-people-gather'),
                $role_select = $gather.find('#uw-added-users-role'),
                $section_select = $gather.find('#uw-added-users-section'),
                $button = $modal.find('button#uw-add-people-validate');

            $('#uw-add-people-slightofhand').find('.ReactModalPortal').hide();

            // reset modal
            $gather.find('#uw-users-to-add').val('');
            $role_select.val($role_select.find('option:first').val());
            $section_select.val($section_select.find('option:first').val());
            showPeopleGather($modal);
        };

        function launchAddPeople() {
            var tpl = Handlebars.templates['add_users'],
                $modal,
                $confirm,
                $progressbar;

            $('head').append('<link rel="stylesheet" type="text/css" href="'
                             + window.canvas_users.css + '"/>'
                             + '<style>'
                             + '.uw-add-user-timedout-icon { background-image: url('
                             + window.canvas_users.images + 'circle_bang.png' + ')}'
                             + '.uw-add-user-problem-icon { background-image: url('
                             + window.canvas_users.images + 'circle_bang.png' +')}'
                             + '</style>');

            $modal = $('#uw-add-people-slightofhand');
            $modal.append($(tpl()));
            $modal.find('button#uw-add-people-validate').on('click', validateUsers);
            $modal.delegate('input, textarea, select', 'focus',
                                     function (e) {
                                         $(e.target).closest('.ic-Form-control')
                                             .removeClass('ic-Form-control--has-error');
                                     });
            $modal.find('#uw-users-to-add').on('keyup', validatableUsers);
            $modal.find('#uw-added-users-section,'
                        + '#uw-added-users-role').on('change', validatableUsers);
            $modal.find('button.uw-add-people-close').on('click', finishAddPeople);

            $modal.find('button#uw-add-people-startover').on('click', startOver);
            $modal.find('button#uw-add-people-import').on('click', confirmFERPA);

            $confirm = $modal.find('button#uw-add-people-ferpa-confirm');
            $confirm.on('click', importUsers);
            $modal.find('div.uw-add-people-ferpa #confirmed').on('change', function () {
                if ($(this).is(':checked')) {
                    $confirm.removeProp('disabled');
                } else {
                    $confirm.prop('disabled', true);
                }
            });

            $('#uw-add-people-slightofhand .ReactModal__Content')
                .on('mousewheel DOMMouseScroll', function (e) {
                    var $node = $(e.target);

                    if (!($node.closest('.uw-add-people-validation-scrolled').length === 1
                          || $node.closest('.uw-users-to-add') === 1)) {
                        e.stopPropagation();
                        e.preventDefault();
                    }
                });

            $modal.find('.uw-add-people-confirm '
                        + '.uw-add-people-progress-overlay')
                .on('click', function (e) {
                    e.stopPropagation();
                    e.preventDefault();
                });

            showPeopleGather($modal);

            loadCourseRoles(window.canvas_users.canvas_account_id, $modal);
            loadCourseSections(window.canvas_users.canvas_course_id, $modal);
        };

        launchAddPeople();

        $('#addUsers').removeAttr('disabled');
    });
}(jQuery));
