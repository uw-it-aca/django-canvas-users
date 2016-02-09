(function() {
  var template = Handlebars.template, templates = Handlebars.templates = Handlebars.templates || {};
templates['failure_modal'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<div class=\"content-box\">\n  <div class=\"grid-row delayed\">\n    <div class=\"col-sm-2 uw-add-user-problem-icon\"></div>\n    <div class=\"col-sm-10\">\n      <div>\n        <p class=\"bad-result\">\n          We're terribly sorry, but it appears we're unable to add users at this time.\n        </p>\n        <p>\n          Please click <span class=\"start-over\">Start Over to give it another try now, or </span>Close to try again later.\n          <div class=\"hidden\">\n            Reported Error: ";
  if (helper = helpers.error_message) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.error_message); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\n          </div>\n        </p>\n      </div>\n    </div>\n  </div>\n</div>\n";
  return buffer;
  });
})();