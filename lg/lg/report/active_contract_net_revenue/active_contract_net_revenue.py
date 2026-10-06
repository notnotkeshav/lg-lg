# Copyright (c) 2026, extension and contributors
# For license information, please see license.txt

import datetime

import frappe
from frappe import _
from frappe.utils import cint, flt, get_last_day, getdate, nowdate

MONTHS = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
]


def execute(filters=None):
	filters = frappe._dict(filters or {})
	today = getdate(nowdate())
	month = MONTHS.index(filters.month) + 1 if filters.month in MONTHS else today.month
	year = cint(filters.year) or today.year
	filters.month_start = datetime.date(year, month, 1)
	filters.month_end = getdate(get_last_day(filters.month_start))
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Contract"), "fieldname": "contract", "fieldtype": "Link", "options": "CRM Contract", "width": 160},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "CRM Organization", "width": 200},
		{"label": _("Region"), "fieldname": "region", "fieldtype": "Link", "options": "Region Master", "width": 110},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Region Branches", "width": 110},
		{"label": _("Start Date"), "fieldname": "start_date", "fieldtype": "Date", "width": 110},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 110},
		{"label": _("Contract Days"), "fieldname": "contract_days", "fieldtype": "Int", "width": 110},
		{"label": _("Contract Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 140},
		{"label": _("Active Days"), "fieldname": "active_days", "fieldtype": "Int", "width": 100},
		{"label": _("Net Revenue"), "fieldname": "net_revenue", "fieldtype": "Currency", "width": 160},
	]


def get_data(filters):
	"""
	Contracts running at any point in the selected month. Net revenue is the per-day amount
	times 30 for a contract active the whole month, or times its active days when it starts or
	expires mid-month.
	"""
	conditions = [
		"c.docstatus < 2",
		"IFNULL(c.custom_contract_status, '') != 'Rejected'",
		"c.start_date <= %(month_end)s",
		"c.expiry_date >= %(month_start)s",
	]
	for key in ("customer", "region", "branch"):
		if filters.get(key):
			conditions.append(f"c.{key} = %({key})s")

	contracts = frappe.db.sql(
		f"""
		SELECT c.name AS contract, c.customer, c.region, c.branch,
			c.start_date, c.expiry_date, c.amount
		FROM `tabCRM Contract` c
		WHERE {" AND ".join(conditions)}
		ORDER BY c.start_date, c.name
		""",
		filters,
		as_dict=True,
	)

	for row in contracts:
		# Start and expiry dates are both inclusive
		start, expiry = getdate(row.start_date), getdate(row.expiry_date)
		row.contract_days = (expiry - start).days + 1
		if start <= filters.month_start and expiry >= filters.month_end:
			row.active_days = 30
		else:
			row.active_days = (min(expiry, filters.month_end) - max(start, filters.month_start)).days + 1
		row.net_revenue = flt(row.amount) / row.contract_days * row.active_days
	return contracts
