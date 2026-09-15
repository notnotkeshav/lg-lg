app_name = "lg"
app_title = "Lg"
app_publisher = "extension"
app_description = "LG Customization"
app_email = "deepak@extensioncrm.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "lg",
# 		"logo": "/assets/lg/logo.png",
# 		"title": "Lg",
# 		"route": "/lg",
# 		"has_permission": "lg.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "lg.bundle.css"
app_include_js = [
    "notification.bundle.js",
    "change_labels.js"
]

# app_include_js = "/assets/lg/js/lg.js"

# include js, css files in header of web template
# web_include_css = "/assets/lg/css/lg.css"
# web_include_js = "/assets/lg/js/lg.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lg/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "lg/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "lg.utils.jinja_methods",
# 	"filters": "lg.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "lg.install.before_install"
# after_install = "lg.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "lg.uninstall.before_uninstall"
# after_uninstall = "lg.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "lg.utils.before_app_install"
# after_app_install = "lg.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "lg.utils.before_app_uninstall"
# after_app_uninstall = "lg.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lg.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "CRM Deal": "lg.lg.doctype.crm_deal.crm_deal.CRMDeal"
}

    # apps/lg/lg/lg/doctype/crm_deal/crm_deal.py

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------
scheduler_events = {
    "daily": [
        "lg.api.update_all_deal_status.update_all_deal_statuses",
        "lg.lg.doctype.crm_quotation.crm_quotation.check_advance_payment_reminders",
        "lg.lg.doctype.crm_contract.crm_contract.check_advance_payment_reminders",
        "lg.lg.doctype.crm_contract.crm_contract.check_billing_schedule_and_notify",
        "lg.lg.doctype.crm_deal.crm_deal.mark_deals_as_lost",
        "lg.lg.doctype.invoice.invoice.update_invoice_outstanding_per_portion",
        "lg.lg.doctype.crm_contract.crm_contract.set_status_expired",



    ]
}

# scheduler_events = {
# 	"all": [
# 		"lg.tasks.all"
# 	],
# 	"daily": [
# 		"lg.tasks.daily"
# 	],
# 	"hourly": [
# 		"lg.tasks.hourly"
# 	],
# 	"weekly": [
# 		"lg.tasks.weekly"
# 	],
# 	"monthly": [
# 		"lg.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "lg.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "lg.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lg.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lg.utils.before_request"]
# after_request = ["lg.utils.after_request"]

# Job Events
# ----------
# before_job = ["lg.utils.before_job"]
# after_job = ["lg.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"lg.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Custom Field and Property Setter are deliberately NOT fixtures.
#
# Fixtures are a snapshot of whichever site they were last exported from, with
# `filters: []` grabbing every record on that site regardless of which app owns
# it. That snapshot silently drifts from the database, and anything missing from
# it is lost on a fresh install or restore.
#
# Instead:
#   * DocTypes owned by lg carry their fields and properties directly in
#     lg/lg/doctype/<name>/<name>.json.
#   * DocTypes owned by frappe/crm are customized through
#     lg/lg/custom/<name>.json, which bench migrate re-applies on every run.
fixtures = [
    {"dt": "Client Script", "filters": []}
]

website_route_rules = [{'from_route': '/dashboard/<path:app_path>', 'to_route': 'dashboard'}, {'from_route': '/frontend/<path:app_path>', 'to_route': 'frontend'}, {'from_route': '/lgcrm/<path:app_path>', 'to_route': 'lgcrm'}, {'from_route': '/frontend/<path:app_path>', 'to_route': 'frontend'}, {'from_route': '/frontend/<path:app_path>', 'to_route': 'frontend'},]

# website_route_rules = [
#     { "from_route": "/dashboard/<path:app_path>", "to_route":"dashboard"}
# ]