# Copyright (c) 2026, extension and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_months, date_diff, flt, get_first_day, getdate, nowdate

DUE_THIS_MONTH = "Due This Month"
OVERDUE = "Overdue"
PARTIALLY_PAID = "Partially Paid"
CATEGORIES = (OVERDUE, PARTIALLY_PAID, DUE_THIS_MONTH)

NOT_YET_DUE = "Not Yet Due"
AGEING_BUCKETS = ((30, "1-30 Days"), (60, "31-60 Days"), (90, "61-90 Days"), (None, "90+ Days"))


def execute(filters=None):
	filters = frappe._dict(filters or {})
	for key in ("category", "region", "branch"):
		filters[key] = as_list(filters.get(key))
	data = get_data(filters)
	if not data:
		return get_columns(), []

	return get_columns(), data, get_message(), get_chart(data, filters.chart_by), get_report_summary(data)


def as_list(value):
	"""Filters may come as a single value, a list, or a JSON list (from the dashboard multi-selects)."""
	if not value:
		return []
	if isinstance(value, str):
		value = frappe.parse_json(value) if value.startswith("[") else [value]
	return [v for v in value if v]


def get_columns():
	return [
		{"label": _("Contract ID"), "fieldname": "contract_id", "fieldtype": "Link", "options": "CRM Contract", "width": 150},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "CRM Organization", "width": 180},
		{"label": _("Region"), "fieldname": "region", "fieldtype": "Link", "options": "Region Master", "width": 110},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Region Branches", "width": 110},
		{"label": _("ASM Name"), "fieldname": "asm_name", "fieldtype": "Data", "width": 150},
		{"label": _("Billing Term"), "fieldname": "billing_term", "fieldtype": "Data", "width": 110},
		{"label": _("Billing Date"), "fieldname": "billing_date", "fieldtype": "Date", "width": 100},
		{"label": _("Billing Amount"), "fieldname": "billing_amount", "fieldtype": "Currency", "width": 120, "disable_total": 1},
		{"label": _("Billing Status"), "fieldname": "billing_status", "fieldtype": "Data", "width": 110},
		{"label": _("Invoice No"), "fieldname": "invoice_no", "fieldtype": "Data", "width": 120},
		{"label": _("Billed Date"), "fieldname": "billed_date", "fieldtype": "Date", "width": 100},
		{"label": _("Portion %"), "fieldname": "portion", "fieldtype": "Percent", "width": 80, "disable_total": 1},
		{"label": _("Due Date"), "fieldname": "due_date", "fieldtype": "Date", "width": 100},
		{"label": _("Due Amount"), "fieldname": "portion_amount", "fieldtype": "Currency", "width": 120},
		{"label": _("Received Amount"), "fieldname": "amount_received", "fieldtype": "Currency", "width": 120},
		{"label": _("Outstanding"), "fieldname": "outstanding", "fieldtype": "Currency", "width": 120},
		{"label": _("Days Overdue"), "fieldname": "days_overdue", "fieldtype": "Int", "width": 90, "disable_total": 1},
		{"label": _("Ageing"), "fieldname": "ageing", "fieldtype": "Data", "width": 100},
		{"label": _("Category"), "fieldname": "category", "fieldtype": "Data", "width": 120},
	]


def get_data(filters):
	as_on = getdate(filters.as_on_date or nowdate())
	month_start = get_first_day(as_on)
	next_month_start = get_first_day(add_months(as_on, 1))

	conditions = ["b.status IN ('Invoice Raised', 'Partially Paid')"]
	for key, column in (
		("contract", "c.name"),
		("customer", "c.customer"),
		("project", "c.project"),
	):
		if filters.get(key):
			conditions.append(f"{column} = %({key})s")
	for key, column in (("region", "c.region"), ("branch", "c.branch")):
		if filters.get(key):
			conditions.append(f"{column} IN %({key})s")

	# One row per invoice payment-term portion of an invoiced billing row. The billing row
	# points at its Invoice via invoice_link; older rows only carry the invoice number.
	rows = frappe.db.sql(
		f"""
		SELECT
			c.name AS contract_id, c.customer, c.project, c.region, c.branch, c.asm_name,
			b.billing_term, b.billing_date, b.amount AS billing_amount,
			b.status AS billing_status, b.invoice_id AS invoice_no, b.billed_date,
			i.name AS invoice,
			t.portion, t.due_date, t.portion_amount, t.amount_received
		FROM `tabContract Billing Schedule` b
		JOIN `tabCRM Contract` c
			ON c.name = b.parent AND b.parenttype = 'CRM Contract'
		JOIN `tabInvoice` i
			ON i.name = b.invoice_link
			OR (IFNULL(b.invoice_link, '') = '' AND i.invoice = b.invoice_id AND i.amc_contract_id = c.name)
		JOIN `tabInvoice Payment Term` t
			ON t.parent = i.name AND t.parenttype = 'Invoice'
		WHERE {" AND ".join(conditions)}
		ORDER BY t.due_date, c.name, b.billing_date, t.idx
		""",
		filters,
		as_dict=True,
	)

	data = []
	for row in rows:
		row.portion_amount = flt(row.portion_amount)
		row.amount_received = flt(row.amount_received)
		row.outstanding = row.portion_amount - row.amount_received
		if row.outstanding <= 0:
			continue

		due_date = getdate(row.due_date) if row.due_date else None
		if row.amount_received > 0:
			# Some payment came in but part of this portion is still pending
			row.category = PARTIALLY_PAID
		elif due_date and due_date < as_on:
			row.category = OVERDUE
		elif due_date and month_start <= due_date < next_month_start:
			row.category = DUE_THIS_MONTH
		else:
			# Not yet due (future month) and nothing received
			continue

		row.days_overdue = max(date_diff(as_on, due_date), 0) if due_date else 0
		row.ageing = get_ageing_bucket(row.days_overdue)

		if filters.category and row.category not in filters.category:
			continue
		data.append(row)

	return data


def get_ageing_bucket(days_overdue):
	if not days_overdue:
		return NOT_YET_DUE
	for limit, label in AGEING_BUCKETS:
		if limit is None or days_overdue <= limit:
			return label


def get_message():
	return _(
		"Outstanding invoice portions as on the selected date. "
		"<b>Overdue</b>: due date passed, nothing received &middot; "
		"<b>Partially Paid</b>: some amount received, balance pending &middot; "
		"<b>Due This Month</b>: falls due later this month."
	)


CATEGORY_COLORS = ["#ef4444", "#f59e0b", "#3b82f6"]
TOP_N = 10


def get_chart(data, chart_by=None):
	"""Outstanding amount by the chosen dimension, stacked by category (or a category donut)."""
	chart_by = chart_by or "Ageing"
	if chart_by == "Category":
		totals = dict.fromkeys(CATEGORIES, 0.0)
		for row in data:
			totals[row.category] += row.outstanding
		return {
			"data": {
				"labels": [_(category) for category in CATEGORIES],
				"datasets": [{"name": _("Outstanding"), "values": [flt(totals[c], 2) for c in CATEGORIES]}],
			},
			"type": "donut",
			"fieldtype": "Currency",
			"colors": CATEGORY_COLORS,
			"height": 280,
		}

	get_key = {
		"Ageing": lambda row: row.ageing,
		"Customer": lambda row: row.customer,
		"Region": lambda row: row.region,
		"Branch": lambda row: row.branch,
		"Due Month": lambda row: get_first_day(row.due_date) if row.due_date else None,
	}.get(chart_by, lambda row: row.ageing)

	totals = {}
	for row in data:
		key = get_key(row) or _("Not Set")
		totals.setdefault(key, dict.fromkeys(CATEGORIES, 0.0))[row.category] += row.outstanding

	if chart_by == "Ageing":
		keys = [label for label in [NOT_YET_DUE] + [label for _limit, label in AGEING_BUCKETS] if label in totals]
		labels = [_(key) for key in keys]
	elif chart_by == "Due Month":
		keys = sorted(totals, key=lambda k: (isinstance(k, str), str(k)))
		labels = [k if isinstance(k, str) else k.strftime("%b-%Y") for k in keys]
	else:
		# Biggest outstanding first; everything past the top few is folded into "Others"
		keys = sorted(totals, key=lambda k: sum(totals[k].values()), reverse=True)
		if len(keys) > TOP_N:
			others = dict.fromkeys(CATEGORIES, 0.0)
			for key in keys[TOP_N - 1 :]:
				for category in CATEGORIES:
					others[category] += totals[key][category]
			keys = keys[: TOP_N - 1] + [_("Others")]
			totals[keys[-1]] = others
		labels = keys

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _(category), "values": [flt(totals[key][category], 2) for key in keys]}
				for category in CATEGORIES
			],
		},
		"type": "bar",
		"fieldtype": "Currency",
		"colors": CATEGORY_COLORS,
		"barOptions": {"stacked": 1},
		"height": 280,
	}


def get_report_summary(data):
	outstanding = {category: 0.0 for category in CATEGORIES}
	for row in data:
		outstanding[row.category] += row.outstanding

	total_outstanding = sum(outstanding.values())
	due = sum(row.portion_amount for row in data)
	received = sum(row.amount_received for row in data)
	overdue_90 = sum(row.outstanding for row in data if row.days_overdue > 90)
	contracts = len({row.contract_id for row in data})

	return [
		{"label": _("Total Outstanding"), "value": total_outstanding, "datatype": "Currency", "indicator": "Red" if total_outstanding else "Green"},
		{"label": _("Overdue"), "value": outstanding[OVERDUE], "datatype": "Currency", "indicator": "Red"},
		{"label": _("Partially Paid - Balance"), "value": outstanding[PARTIALLY_PAID], "datatype": "Currency", "indicator": "Orange"},
		{"label": _("Due This Month"), "value": outstanding[DUE_THIS_MONTH], "datatype": "Currency", "indicator": "Blue"},
		{"label": _("Overdue 90+ Days"), "value": overdue_90, "datatype": "Currency", "indicator": "Red" if overdue_90 else "Green"},
		{"label": _("Collected on These Dues"), "value": flt(received / due * 100, 2) if due else 0, "datatype": "Percent", "indicator": "Green"},
		{"label": _("Contracts"), "value": contracts, "datatype": "Int", "indicator": "Grey"},
	]
