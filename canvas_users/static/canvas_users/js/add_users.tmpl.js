(function() {
  var template = Handlebars.template, templates = Handlebars.templates = Handlebars.templates || {};
templates['add_users'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  


  return "<div class=\"ReactModalPortal\">\n  <div x-data-reactid=\".1\" class=\"ReactModal__Overlay ReactModal__Overlay--after-open ReactModal__Overlay--canvas\" style=\"background-color: rgba(0, 0, 0, 0.498039);\">\n    <div style=\"position:static;top:0px;left:0px;right:auto;bottom:auto;border-radius:0px;border:none;padding:0px;\" class=\"ReactModal__Content ReactModal__Content--after-open ReactModal__Content--canvas\" tabindex=\"-1\" x-data-reactid=\".1.0\">\n      <div class=\"ReactModal__Layout\" x-data-reactid=\".1.0.0\">\n        <div class=\"ReactModal__Header\" x-data-reactid=\".1.0.0.0\">\n          <div class=\"ReactModal__Header-Title\" x-data-reactid=\".1.0.0.0.0\">\n            <h4 x-data-reactid=\".1.0.0.0.0.0\">Add People</h4>\n          </div>\n          <div class=\"ReactModal__Header-Actions\" x-data-reactid=\".1.0.0.0.1\">\n            <button class=\"Button Button--icon-action uw-add-people-close\" type=\"button\" x-data-reactid=\".1.0.0.0.1.0\">\n              <i class=\"icon-x\" x-data-reactid=\".1.0.0.0.1.0.0\">\n              </i>\n              <span class=\"screenreader-only\" x-data-reactid=\".1.0.0.0.1.0.1\">Close\n              </span>\n            </button>\n          </div>\n        </div>\n        <div class=\"ReactModal__Body\" x-data-reactid=\".1.0.0.1\">\n          <div class=\"content-box\">\n          <div class=\"uw-add-people-gather\">\n            <form>\n                <div class=\"grid-row\">\n                  <div class=\"col-xs-12\">\n                    <label class=\"control-label\" for=\"uw-users-to-add\">Enter UW NetIDs or Gmail addresses, separated by a comma or space</label>\n                  </div>\n                </div>\n                <div class=\"grid-row\">\n                  <div class=\"col-xs-12\">\n                    <textarea id=\"uw-users-to-add\" class=\"ic-Form-control\" placeholder=\"netid, netid, googleid@gmail.com\" aria-label=\"Enter the email addresses of the users you would like to add, seperated by commas or spaces\"></textarea>\n                  </div>\n                </div>\n                <div class=\"grid-row\">\n                  <div class=\"col-xs-6 ic-Form-control\">\n                    <label class=\"control-label\" for=\"uw-added-users-section\">Select section</label>\n                    <select id=\"uw-added-users-section\" class=\"uw-add-people-loading\" disabled>\n                      <option value=\"\">Loading&hellip;</option>\n                    </select><span class=\"uw-add-people-working\" style=\"display:none;\"><i class=\"icon-refresh\"></i></span>\n                  </div>\n                  <div class=\"col-xs-6 ic-Form-control\">\n                    <label class=\"control-label\" for=\"uw-added-users-role\">Select role</label>\n                    <select id=\"uw-added-users-role\" class=\"loading uw-add-people-loading\" disabled>\n                      <option value=\"\">Loading&hellip;</option>\n                    </select><span class=\"uw-add-people-working\" style=\"display:none;\"><i class=\"icon-refresh\"></i></span>\n                  </div>\n                </div>\n            </form>\n          </div>\n          <div class=\"uw-add-people-confirm\" style=\"display:none;\"></div>\n          <div class=\"uw-add-people-problem\" style=\"display:none;\"></div>\n          <div class=\"uw-add-people-timedout\" style=\"display:none;\">\n            <div class=\"row delayed\">\n              <div class=\"col-sm-2 text-right\">\n                <span class=\"fa-stack warning\">\n                  <i class=\"fa fa-circle-thin fa-stack-2x\"></i>\n                  <i class=\"fa fa-exclamation fa-stack-1x\"></i>\n                </span>\n              </div>\n              <div class=\"col-sm-10\">\n                <div>\n                  <p>\n                    We're adding your users, but Canvas is responding slowly.\n                  </p><p>\n                    Please check the People page in a few minutes to verify that your new users have been added.\n                  </p>\n                </div>\n              </div>\n            </div>\n          </div>\n          <div class=\"uw-add-people-ferpa\" style=\"display:none;\">\n            <h4>FERPA Acknowledgement</h4>\n            <p>\n              The Family Educational Rights and Privacy Act (FERPA) of 1974 protects the privacy of students' education records. Generally, the University and its employees may not release or share a student's educational records, or information from a student's education records, unless it has the student's written consent to do so. Some exceptions to this general rule can be found at <a href=\"http://www.washington.edu/students/reg/ferpafac.html\" target=\"_blank\">FERPA for Faculty and Staff</a>. It is important that you understand when it is appropriate and allowable to release information from students' education records to third parties, such as faculty, staff, parents, and other students.\n            </p>\n            <div class=\"ic-Checkbox-group\">\n              <div class=\"ic-Form-control ic-Form-control--checkbox\">\n                <input type=\"checkbox\" id=\"confirmed\">\n                <label class=\"ic-Label\" for=\"confirmed\">I understand</label>\n              </div>\n            </div>\n          </div>\n          </div>\n        </div>\n        <div class=\"ReactModal__Footer\" x-data-reactid=\".1.0.0.2\">\n          <div class=\"ReactModal__Footer-Actions\" x-data-reactid=\".1.0.0.2.0\">\n            <button type=\"button\" id=\"uw-add-people-startover\" class=\"Button uw-add-people-confirm uw-add-people-ferpa uw-add-people-problem\" style=\"display:none;\">Start Over</button>\n            <button type=\"button\" id=\"uw-add-people-validate\" class=\"Button Button--primary uw-add-people-gather\" disabled style=\"display:none;\">Next</button><span class=\"uw-add-people-working\" style=\"display:none;\"><i class=\"icon-refresh\"></i></span>\n            <button type=\"button\" id=\"uw-add-people-import\" class=\"Button Button--primary uw-add-people-confirm\" style=\"display:none;\">Add Users</button>\n            <button type=\"button\" id=\"uw-add-people-ferpa-confirm\" class=\"Button Button--primary uw-add-people-ferpa\" disabled style=\"display:none;\">Confirm</button>\n            <button type=\"button\" class=\"Button Button--primary uw-add-people-close uw-add-people-timedout uw-add-people-problem\" data-dismiss=\"modal\" style=\"display:none;\">Done</button>\n          </div>\n        </div>\n      </div>\n    </div>\n  </div>\n</div>\n";
  });
})();