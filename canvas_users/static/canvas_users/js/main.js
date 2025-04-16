/*jslint browser: true, plusplus: true, unparam: true, esversion: 6 */
/*global jQuery, Handlebars, top */


(function ($) {
    "use strict";
    $(document).ready(function () {

        const ferpa_base_roles = ['TeacherEnrollment', 'TaEnrollment', 'DesignerEnrollment'],
              confirmSelector = '.uw-add-people-confirm',
              gatherSelector = '.uw-add-people-gather',
              timedoutSelector = '.uw-add-people-timedout',
              problemSelector = '.uw-add-people-problem',
              ferpaSelector = '.uw-add-people-ferpa',
              registrationRequirementsSelector = '.uw-add-people-registration-requirements',
              acceptanceSelector = '.uw-add-people-accept',
              progressOverlaySelector = 'div.uw-add-people-progress-overlay',
              noticeCheckboxSelector = 'input#uw-add-people-notice-is-confirmed',
              importButtonSelector = 'button#uw-add-people-import',
              validateButtonSelector = 'button#uw-add-people-validate',
              closeButtonSelector = 'button.uw-add-people-close',
              startOverButtonSelector = 'button#uw-add-people-startover';

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
                if (window.canvas_users.hasOwnProperty('csrftoken') &&
                        window.canvas_users.csrftoken &&
                        !csrfSafeMethod(settings.type)) {
                    xhr.setRequestHeader("X-CSRFToken", window.canvas_users.csrftoken);
                }
            }
        });

        function getModal(e) {
            return $(e.target).closest('.ReactModal__Content');
        }

        function hideModalPanels($modal) {
            var modals = [gatherSelector, confirmSelector,
                          problemSelector, timedoutSelector,
                          ferpaSelector, registrationRequirementsSelector];

            $modal.find(modals.join(',')).hide();
        }

        function showPeopleGather($modal) {
            hideModalPanels($modal);
            $modal.find(gatherSelector).show();
            validateGatherForm($modal);
            $modal.find('#uw-users-to-add').focus();
        }

        function showPeopleConfirmation($modal) {
            hideModalPanels($modal);
            $modal.find(confirmSelector).show();
            $modal.find(importButtonSelector).focus();
        }

        function showPeopleAcceptanceModal($modal, selector) {
            hideModalPanels($modal);
            $modal.find(selector).show();
            $modal.find('button' + acceptanceSelector).attr('disabled', true);
            $modal.find('input' + acceptanceSelector).removeAttr('checked').focus();
        }

        function showPeopleTimedOut($modal) {
            hideModalPanels($modal);
            $modal.find(timedoutSelector).show();
        }

        function showPeopleProblem($modal) {
            hideModalPanels($modal);
            $modal.find(problemSelector).show();
        }

        function startOver(e) {
            var $modal = getModal(e);

            e.stopPropagation();
            showPeopleGather($modal);
        }

        function problemAddingUsers(msg, $modal) {
            var tpl = Handlebars.templates.failure_modal,
                error_json,
                error_text = '';

            try {
                error_json = JSON.parse(msg).error;
                error_text = error_json.msg.status.toUpperCase() + ' (' +
                    error_json.msg.errors[0].message + ')';
            } catch (e) {
                error_text = msg;
            }

            $modal.find('div' + problemSelector).html(tpl({
                error_message: error_text
            }));

            showPeopleProblem($modal);
        }

        function timeoutAddingUsers($modal) {
            showPeopleTimedOut($modal);
        }

        function canvasFlashMessage(type, message) {
            var $holder = $('#flash_message_holder'),
                $li = $('<li class="ic-flash-' + type + '" style="z-index: 2;">' +
                        '<div class="ic-flash__icon" aria-hidden="true"><i class="icon-check"></i></div>' +
                        message +
                        '<button type="button" class="Button Button--icon-action close_link">' +
                        '<span class="screenreader-only">Close</span>' +
                        '<i class="icon-x" aria-hidden="true"></i></button></li>');

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

        function finishAddPeople(e) {
            finishAddPeopleModal(getModal(e));
        }

        function finishImport(count, role, $modal) {
            finishAddPeopleModal($modal);
            canvasFlashMessage('success',
                               'Added ' + count + ' ' + role +
                               ((count > 1) ? 's' : ''));
        }

        function importUsers(e) {
            var $modal = getModal(e),
                $modalbox = $modal.find('.ReactModal__Layout'),
                $progressbaroverlay = $modal.find(['div' + confirmSelector,  progressOverlaySelector].join(' ')),
                $progressbar = $progressbaroverlay.find('#progressbar'),
                $progressbarlabel = $progressbaroverlay.find('#progressbar .progress-label'),
                context = window.canvas_users.validated_context,
                logins = [],
                start_value = Math.floor(Math.random() * 10);

            e.stopPropagation();
            e.preventDefault();

            showPeopleConfirmation($modal);

            $progressbaroverlay.show();
            $progressbar.progressbar({
                value: start_value,
                change: function () {
                    $progressbarlabel.text($progressbar.progressbar('value') + '%');
                }
            });

            $progressbaroverlay.offset({
                top: $modalbox.offset().top,
                left: $modalbox.offset().left
            });
            $progressbaroverlay.css('height', $modalbox.height());
            $progressbaroverlay.css('width', $modalbox.width());

            $progressbarlabel.text(start_value + '%');

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
                url: 'https://' +
                    window.canvas_users.canvas_users_host +
                    '/users/api/v1/canvas/course/' +
                    window.canvas_users.canvas_course_id + '/import',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    logins: logins,
                    role: context.role,
                    role_id: context.role_id,
                    role_base: context.role_base,
                    course_id: window.canvas_users.canvas_course_id,
                    course_sis_id: window.canvas_users.sis_course_id,
                    section_id: context.section_id,
                    section_sis_id: context.section_sis_id,
                    section_only: context.section_only,
                    notify_users: context.notify_users
                })
            })
                .done(function (data) {
                    if (data.import_id === null) {
                        finishImport(logins.length, context.role, $modal);
                    } else {
                        monitorImport(data.import_id, logins.length, context.role, $modal);
                    }
                })
                .fail(function (msg) {
                    problemAddingUsers(msg.resonseText, $modal);
                });
        }

        function confirmImport(e) {
            var $modal = getModal(e),
                context = window.canvas_users.validated_context;

            e.stopPropagation();
            e.preventDefault();

            if (ferpa_base_roles.indexOf(context.role_base) >= 0) {
                showPeopleAcceptanceModal($modal, ferpaSelector);
            } else if (context.role_base === 'StudentEnrollment' && is_academic_course()) {
                showPeopleAcceptanceModal($modal, registrationRequirementsSelector);
            } else {
                importUsers(e);
            }
        }

        function is_academic_course() {
            var sis_re = /^\d{4}-(winter|spring|summer|autumn)-[\w& ]+-\d{3}-[A-Z][A-Z0-9]?(-[A-F0-9]{32})?$/;

            return sis_re.test(window.canvas_users.sis_course_id);
        }

        function monitorImport(import_id, user_count, role, $modal) {
            var $progressbar = $modal.find(progressOverlaySelector + ' #progressbar'),
                current_percent = $progressbar.progressbar('value'),
                initial_percent = current_percent + Math.floor((100 - current_percent) / (user_count + 1)),
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
                    problemAddingUsers(msg.responseText, $modal);
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
                url: 'https://' +
                    window.canvas_users.canvas_users_host +
                    '/users/api/v1/canvas/course/' +
                    window.canvas_users.canvas_course_id +
                    '/import?import_id=' + import_id
            })
                .done(function (data) {
                    var progress = parseInt(data.progress, 10);

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

        function validatableUsers(e) {
            validateGatherForm(getModal(e));
        }

        function validateGatherForm($modal) {
            var $button = $modal.find(validateButtonSelector);

            if ($modal.find('#uw-users-to-add').val().trim().length &&
                    $modal.find('#uw-added-users-role option:selected').val().length &&
                    $modal.find('#uw-added-users-section option:selected').val().length) {
                $button.removeAttr('disabled');
            } else {
                $button.attr('disabled', true);
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
                section_only = ($modal.find('#section-only:checked').length === 1),
                notify_users = ($modal.find('#notify-users:checked').length === 1),
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

            $modal.find(validateButtonSelector).addClass('uw-add-people-loading').attr('disabled', true);
            $(gatherSelector, $modal).find('input, button, select, textarea').attr('disabled', true);

            $.ajax({
                type: 'POST',
                url: 'https://' +
                    window.canvas_users.canvas_users_host +
                    '/users/api/v1/canvas/course/' +
                    window.canvas_users.canvas_course_id +
                    '/validate',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    login_ids: users_to_add,
                    role_id: add_as_role_vals[0],
                    role_base: add_as_role_vals[1],
                    section_id: add_to_section_vals[0],
                    section_sis_id: add_to_section_vals[1]
                })
            })
                .done(function (data) {
                    var tpl = Handlebars.templates.validate_users,
                        tpl_button = Handlebars.templates.add_users_button,
                        valid_context,
                        validated_users = [],
                        validated_user_count = 0;

                    $.each(data.users, function () {
                        var comment = this.comment;
                        if (this.status === 'valid') {
                            validated_user_count++;
                        } else if (comment === 'UWNetID not permitted') {
                            comment = 'Not authorized to login to Canvas. <a target="_blank" title="Canvas access policies" href="https://itconnect.uw.edu/learn/tools/canvas/canvas-policies/access/">Learn more</a>';
                        }

                        validated_users.push({
                            add: (this.status === 'valid'),
                            present: (this.status === 'present'),
                            invalid: (this.status === 'invalid'),
                            login: this.login,
                            regid: this.regid,
                            name: this.name,
                            comment: comment
                        });
                    });

                    valid_context = {
                        count: validated_user_count,
                        no_logins: (validated_user_count < 1),
                        count_plural: (validated_user_count > 1) ? 's' : '',
                        total_plural: (data.users.length > 1) ? 's' : '',
                        exceptions: (validated_user_count !== data.users.length),
                        total: data.users.length,
                        users: validated_users,
                        role: add_as_role_option.text(),
                        role_id: add_as_role_vals[0],
                        role_base: add_as_role_vals[1],
                        section_name: add_to_section_option.text(),
                        section_id: add_to_section_vals[0],
                        section_sis_id: add_to_section_vals[1],
                        section_only: section_only,
                        notify_users: notify_users
                    };

                    window.canvas_users.validated_context = valid_context;

                    $modal.find('div' + confirmSelector).html(tpl(valid_context));
                    $modal.find(importButtonSelector).html(tpl_button({
                        count: validated_user_count,
                        plural: (validated_user_count === 1) ? '' : 's',
                        role: add_as_role_option.text()
                    }));

                    showPeopleConfirmation($modal);

                    if (validated_user_count === 0) {
                        $modal.find(importButtonSelector).hide();
                        $modal.find(closeButtonSelector).show();
                    }
                })
                .fail(function (msg) {
                    problemAddingUsers(msg.responseText, $modal);
                })
                .always(function () {
                    $modal.find('.uw-add-people-loading').removeClass('uw-add-people-loading');
                    $(gatherSelector, $modal).find('input, button, select, textarea').removeAttr('disabled');
                });
        }

        function loadCourseRoles(account_id, $modal) {
            var $select = $modal.find('#uw-added-users-role');

            $.ajax({
                type: 'GET',
                url: 'https://' +
                    window.canvas_users.canvas_users_host +
                    '/users/api/v1/canvas/account/' + account_id + '/course/roles',
                async: true
            })
                .done(function (data) {
                    var tpl = Handlebars.templates.add_users_role;

                    $select.html(tpl({
                        plural: (data.roles.length > 1),
                        roles: data.roles
                    }));
                })
                .fail(function (msg) {
                    problemAddingUsers(msg.responseText, $modal);
                })
                .always(function () {
                    $select.removeAttr('disabled').removeClass('uw-add-people-loading');
                });
        }

        function loadCourseSections(course_id, $modal) {
            var $select = $modal.find('#uw-added-users-section');

            $.ajax({
                type: 'GET',
                url: 'https://' +
                    window.canvas_users.canvas_users_host +
                    '/users/api/v1/canvas/course/' + course_id + '/sections',
                async: true
            })
                .done(function (data) {
                    var tpl = Handlebars.templates.add_users_section;

                    $select.html(tpl({
                        plural: (data.sections.length > 1),
                        sections: data.sections
                    }));
                })
                .fail(function (msg) {
                    problemAddingUsers(msg.responseText, $modal);
                })
                .always(function () {
                    $select.removeAttr('disabled').removeClass('uw-add-people-loading');
                });
        }

        function finishAddPeopleModal($modal) {
            var $gather = $modal.find('div' + gatherSelector),
                $role_select = $gather.find('#uw-added-users-role'),
                $section_select = $gather.find('#uw-added-users-section');

            $('#uw-add-people-slightofhand').find('.ReactModalPortal').hide();

            // reset modal
            $gather.find('#uw-users-to-add').val('');
            $role_select.val($role_select.find('option:first').val());
            $section_select.val($section_select.find('option:first').val());
            $gather.find('#section-only:checked').removeAttr('checked');
            $gather.find('#notify-users:checked').removeAttr('checked');
            showPeopleGather($modal);
        }

        function launchAddPeople() {
            var tpl = Handlebars.templates.add_users,
                $modal,
                $confirmButton;

            $('head').append('<link rel="stylesheet" type="text/css" href="' +
                             window.canvas_users.css + '"/>' +
                             '<style>' +
                             '.uw-add-user-timedout-icon { background-image: url(' +
                             window.canvas_users.images + 'circle_bang.png' + ')}' +
                             '.uw-add-user-problem-icon { background-image: url(' +
                             window.canvas_users.images + 'circle_bang.png' + ')}' +
                             '</style>');

            $modal = $('#uw-add-people-slightofhand');
            $modal.append($(tpl()));
            $modal.find(validateButtonSelector).on('click', validateUsers);
            $modal.delegate('input, textarea, select', 'focus', function (e) {
                $(e.target)
                    .closest('.ic-Form-control')
                    .removeClass('ic-Form-control--has-error');
            });
            $modal.find('#uw-users-to-add').on('keyup', validatableUsers);
            $modal.find('#uw-added-users-section,' +
                        '#uw-added-users-role').on('change', validatableUsers);
            $modal.find(closeButtonSelector).on('click', finishAddPeople);

            $modal.find(startOverButtonSelector).on('click', startOver);
            $modal.find(importButtonSelector).on('click', confirmImport);

            $confirmButton = $modal.find('button' + acceptanceSelector);
            $confirmButton.on('click', importUsers);
            $modal.find('input' + acceptanceSelector).on('change', function () {
                if ($(this).is(':checked')) {
                    $confirmButton.removeAttr('disabled');
                } else {
                    $confirmButton.attr('disabled', true);
                }
            });

            $('#uw-add-people-slightofhand .ReactModal__Content')
                .on('mousewheel DOMMouseScroll', function (e) {
                    var $node = $(e.target);

                    if (!($node.closest('.uw-add-people-validation-scrolled').length === 1 ||
                              $node.closest('.uw-users-to-add') === 1)) {
                        e.stopPropagation();
                        e.preventDefault();
                    }
                });

            showPeopleGather($modal);

            loadCourseRoles(window.canvas_users.canvas_account_id, $modal);
            loadCourseSections(window.canvas_users.canvas_course_id, $modal);
        }

        launchAddPeople();

        $('#addUsers').removeAttr('disabled');
    });
}(jQuery));
