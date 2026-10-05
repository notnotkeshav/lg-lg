# Copyright (c) 2026, extension and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, add_months, flt, get_first_day, get_last_day, getdate, nowdate

BILLED = "Billed"
NON_BILLED = "Non-Billed"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	today = getdate(nowdate())
	filters.from_date = getdate(filters.from_date or get_first_day(today))
	filters.to_date = getdate(filters.to_date or get_last_day(today))
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be after To Date"))

	data, months, end_position = get_data(filters)
	if not data:
		return get_columns(), []

	return get_columns(), data, get_message(), get_chart(months), get_report_summary(end_position)


def get_columns():
	return [
		{"label": _("Month / Case / Contract"), "fieldname": "label", "fieldtype": "Data", "width": 220},
		{"label": _("Contract ID"), "fieldname": "contract_id", "fieldtype": "Link", "options": "CRM Contract", "width": 140},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "CRM Organization", "width": 180},
		{"label": _("Region"), "fieldname": "region", "fieldtype": "Link", "options": "Region Master", "width": 100},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Region Branches", "width": 100},
		{"label": _("Payment Frequency"), "fieldname": "payment_frequency", "fieldtype": "Data", "width": 110},
		{"label": _("Billing Terms"), "fieldname": "billing_terms", "fieldtype": "Data", "width": 150},
		{"label": _("Oldest Billing Date"), "fieldname": "billing_date", "fieldtype": "Date", "width": 150},
		{"label": _("Days Overdue"), "fieldname": "days_overdue", "fieldtype": "Int", "width": 90},
		{"label": _("Pending Terms (Delay)"), "fieldname": "pending_terms", "fieldtype": "Int", "width": 100},
		{"label": _("Billed Value"), "fieldname": "billed_value", "fieldtype": "Currency", "width": 120},
		{"label": _("Received"), "fieldname": "received", "fieldtype": "Currency", "width": 120},
		{"label": _("Collected %"), "fieldname": "collected_pct", "fieldtype": "Percent", "width": 100},
		{"label": _("Total To Collect"), "fieldname": "to_collect", "fieldtype": "Currency", "width": 150},
		# {"label": _("Monthly Value (Per Day)"), "fieldname": "monthly_value", "fieldtype": "Currency", "width": 140},
	]


def get_data(filters):
	"""
	Returns the tree rows (month -> case -> contract), the month rows shown (for the chart) and the
	month row for the last month of the range, i.e. the position at the end of the range.
	"""
	contracts = get_contracts(filters)
	if not contracts:
		return [], [], None

	terms_by_contract = get_billing_terms(contracts)
	today = getdate(nowdate())
	data, months = [], []
	month_row = None
	total_monthly_value = 0.0

	for window_start, window_end in get_month_windows(filters.from_date, filters.to_date):
		# case -> contract -> aggregated row
		case_rows = {BILLED: {}, NON_BILLED: {}}
		for contract in contracts:
			for term in terms_by_contract.get(contract.name, []):
				add_term(case_rows, contract, term, window_start, window_end)

		as_on = min(window_end, today)
		month_row = {"label": window_start.strftime("%b-%Y"), "indent": 0, **new_totals()}
		month_rows = []
		for case in (BILLED, NON_BILLED):
			if filters.case and filters.case != case:
				continue
			rows = sorted(case_rows[case].values(), key=lambda r: (r["billing_date"], r["contract_id"]))
			case_row = {"label": case, "indent": 1, **new_totals()}
			for row in rows:
				row["billing_terms"] = ", ".join(row["billing_terms"])
				row["days_overdue"] = max((as_on - row["billing_date"]).days, 0)
				add_to_totals(case_row, row)
			add_to_totals(month_row, case_row)
			month_row[case] = case_row
			month_rows.append(case_row)
			month_rows.extend(rows)

		month_row["overdue_90"] = 0.0
		for row in month_rows:
			if row.get("case", row["label"]) == BILLED:
				row["collected_pct"] = collected_pct(row)
			if row["indent"] == 2 and row["days_overdue"] > 90:
				month_row["overdue_90"] += row["to_collect"]

		total_monthly_value += month_row["monthly_value"]
		if not month_row["pending_terms"]:
			# Nothing due or outstanding in this month - skip it rather than showing an empty tree
			continue

		months.append(month_row)
		data.append({k: v for k, v in month_row.items() if k not in (BILLED, NON_BILLED, "overdue_90")})
		data.extend(month_rows)

	if len(months) > 1 or (months and months[-1] is not month_row):
		# Pending amounts carry forward month to month, so the range total is the position at the
		# end of the range; only the per-day monthly value adds up across months.
		data.append({
			"label": _("Total (as on {0})").format(frappe.format(window_end, "Date")),
			"indent": 0,
			"is_total": 1,
			**{key: month_row[key] for key in new_totals()},
			"monthly_value": total_monthly_value,
		})
	if month_row:
		month_row["range_monthly_value"] = total_monthly_value
	return data, months, month_row


def collected_pct(row):
	return flt(flt(row["received"]) / flt(row["billed_value"]) * 100, 2) if row["billed_value"] else 0


def add_term(case_rows, contract, term, window_start, window_end):
	"""Place one billing term under Billed / Non-Billed for the month window ending on window_end."""
	if not term.billing_date or term.billing_date > window_end:
		# Not yet due for billing in this month
		return

	billed_on = term.billed_on
	if billed_on and billed_on <= window_end:
		received = sum(amount for paid_on, amount in term.payments if paid_on <= window_end)
		to_collect = flt(term.invoice_amount) - received
		if to_collect <= 0.005:
			return
		case = BILLED
		billed_value = term.invoice_amount
	else:
		# Billing date is in this month or already passed but invoice not raised yet
		case = NON_BILLED
		received = 0
		billed_value = to_collect = flt(term.amount)

	row = case_rows[case].get(contract.name)
	if not row:
		row = case_rows[case][contract.name] = {
			"label": contract.name,
			"indent": 2,
			"case": case,
			"contract_id": contract.name,
			"customer": contract.customer,
			"region": contract.region,
			"branch": contract.branch,
			"payment_frequency": contract.payment_frequency,
			"billing_terms": [],
			"billing_date": term.billing_date,
			**new_totals(),
		}

	row["billing_terms"].append(term.billing_term or term.billing_date.strftime("%d-%m-%Y"))
	row["billing_date"] = min(row["billing_date"], term.billing_date)
	row["pending_terms"] += 1
	row["billed_value"] += flt(billed_value)
	row["received"] += received
	row["to_collect"] += to_collect
	# billed value / billed period * active days of the period falling in this month
	row["monthly_value"] += flt(billed_value) / term.period_days * overlap_days(
		term.period_from, term.period_to, window_start, window_end
	)


def get_message():
	return _("Pending amounts are the position at each month end.")


def get_chart(months):
	if not months:
		return None

	return {
		"data": {
			"labels": [m["label"] for m in months],
			"datasets": [
				{"name": _("Billed - Awaiting Payment"), "chartType": "bar", "values": [case_value(m, BILLED) for m in months]},
				{"name": _("Due - Not Yet Billed"), "chartType": "bar", "values": [case_value(m, NON_BILLED) for m in months]},
			],
		},
		"type": "axis-mixed",
		"fieldtype": "Currency",
		"colors": ["#8b5cf6", "#14b8a6"],
		"barOptions": {"stacked": 1},
		"height": 280,
	}


def case_value(month_row, case):
	return flt(month_row[case]["to_collect"], 2) if case in month_row else 0


def get_report_summary(end):
	"""KPI cards for the position at the end of the selected range."""
	billed = end.get(BILLED) or new_totals()
	non_billed = end.get(NON_BILLED) or new_totals()
	to_collect = flt(end["to_collect"])

	return [
		{"label": _("Total To Collect"), "value": to_collect, "datatype": "Currency", "indicator": "Red" if to_collect else "Green"},
		{"label": _("Billed - Awaiting Payment"), "value": flt(billed["to_collect"]), "datatype": "Currency", "indicator": "Orange"},
		{"label": _("Due - Not Yet Billed"), "value": flt(non_billed["to_collect"]), "datatype": "Currency", "indicator": "Blue"},
		{"label": _("Collected on Billed"), "value": collected_pct(billed), "datatype": "Percent", "indicator": "Green"},
		{"label": _("Overdue 90+ Days"), "value": end["overdue_90"], "datatype": "Currency", "indicator": "Red" if end["overdue_90"] else "Green"},
	]


def get_contracts(filters):
	conditions = ["c.docstatus < 2"]
	for key, column in (
		("contract", "c.name"),
		("customer", "c.customer"),
		("region", "c.region"),
		("branch", "c.branch"),
	):
		if filters.get(key):
			conditions.append(f"{column} = %({key})s")

	return frappe.db.sql(
		f"""
		SELECT c.name, c.customer, c.region, c.branch, c.payment_frequency, c.billing_terms,
			c.start_date, c.expiry_date
		FROM `tabCRM Contract` c
		WHERE {" AND ".join(conditions)}
			AND EXISTS (
				SELECT 1 FROM `tabContract Billing Schedule` b
				WHERE b.parent = c.name AND b.parenttype = 'CRM Contract'
					AND b.billing_date <= %(to_date)s
			)
		ORDER BY c.name
		""",
		filters,
		as_dict=True,
	)


def get_billing_terms(contracts):
	"""Billing schedule rows per contract, each with its billing period, invoice amount and payments."""
	contract_map = {c.name: c for c in contracts}
	rows = frappe.db.sql(
		"""
		SELECT b.parent, b.billing_term, b.billing_date, b.billed_date, b.amount, b.status,
			b.invoice_id, b.invoice_link, b.is_free, b.is_discountinue,
			b.amount_received, b.payment_received_date
		FROM `tabContract Billing Schedule` b
		WHERE b.parenttype = 'CRM Contract' AND b.parent IN %(contracts)s
			AND b.billing_date IS NOT NULL
		ORDER BY b.parent, b.billing_date, b.idx
		""",
		{"contracts": list(contract_map)},
		as_dict=True,
	)

	invoices = get_invoices(rows)
	terms_by_contract = defaultdict(list)
	for row in rows:
		terms_by_contract[row.parent].append(row)

	for name, terms in terms_by_contract.items():
		set_billing_periods(contract_map[name], terms)
		for term in terms:
			set_invoice_details(term, invoices)
		# Free / discontinued terms only mattered for working out the billing periods
		terms_by_contract[name] = [t for t in terms if not t.is_free and not t.is_discountinue]

	return terms_by_contract


def set_billing_periods(contract, terms):
	"""
	Each billing row covers a period of the contract:
	- Advance billing: billing date is the start of the period (runs till the next billing date).
	- Post billing: billing date is the end of the period (runs from the previous billing date).
	"""
	start = getdate(contract.start_date) if contract.start_date else None
	expiry = getdate(contract.expiry_date) if contract.expiry_date else None
	dates = [getdate(t.billing_date) for t in terms]
	advance = contract.billing_terms == "Advance" or (start and dates[0] == start)

	for i, term in enumerate(terms):
		term.billing_date = dates[i]
		if len(terms) == 1:
			period_from, period_to = start or dates[0], expiry or dates[0]
		elif advance:
			period_from = dates[i]
			period_to = add_days(dates[i + 1], -1) if i + 1 < len(dates) else (expiry or add_days(add_months(dates[i], months_between(dates)), -1))
		else:
			period_from = dates[i - 1] if i else (start or add_months(dates[i], -months_between(dates)))
			period_to = dates[i] if i + 1 == len(dates) else add_days(dates[i], -1)

		term.period_from, term.period_to = getdate(period_from), getdate(period_to)
		if term.period_to < term.period_from:
			term.period_to = term.period_from
		term.period_days = (term.period_to - term.period_from).days + 1


def months_between(dates):
	"""Billing frequency in months, taken from the gap between the first two billing dates."""
	if len(dates) < 2:
		return 12
	return max(round((dates[1] - dates[0]).days / 30.4), 1)


def get_invoices(rows):
	links = {r.invoice_link for r in rows if r.invoice_link}
	numbers = {r.invoice_id for r in rows if r.invoice_id and not r.invoice_link}
	if not links and not numbers:
		return {}

	conditions = []
	if links:
		conditions.append("i.name IN %(links)s")
	if numbers:
		conditions.append("i.invoice IN %(numbers)s")

	invoices = frappe.db.sql(
		f"""
		SELECT i.name, i.invoice, i.amc_contract_id, i.amount_invoiced, i.posting_date
		FROM `tabInvoice` i
		WHERE {" OR ".join(conditions)}
		""",
		{"links": list(links) or [""], "numbers": list(numbers) or [""]},
		as_dict=True,
	)
	if not invoices:
		return {}

	payments = defaultdict(list)
	for p in frappe.db.sql(
		"""
		SELECT parent, portion_amount, amount_received, amount_received_date
		FROM `tabInvoice Payment Term`
		WHERE parenttype = 'Invoice' AND parent IN %(invoices)s
		""",
		{"invoices": [i.name for i in invoices]},
		as_dict=True,
	):
		payments[p.parent].append(p)

	invoice_map = {}
	for invoice in invoices:
		invoice.terms = payments.get(invoice.name, [])
		invoice_map[invoice.name] = invoice
		invoice_map[(invoice.invoice, invoice.amc_contract_id)] = invoice
	return invoice_map


def set_invoice_details(term, invoices):
	"""Work out when the term was billed, its invoiced amount and the dated payments against it."""
	term.billed_on = None
	term.payments = []
	term.invoice_amount = flt(term.amount)
	if term.status == "Pending":
		return

	invoice = invoices.get(term.invoice_link) or invoices.get((term.invoice_id, term.parent))
	term.billed_on = getdate(term.billed_date or (invoice and invoice.posting_date) or term.billing_date)

	if invoice and invoice.terms:
		term.invoice_amount = sum(flt(t.portion_amount) for t in invoice.terms) or flt(invoice.amount_invoiced) or term.invoice_amount
		# Undated receipts are treated as received on the billing day
		term.payments = [
			(getdate(t.amount_received_date) if t.amount_received_date else term.billed_on, flt(t.amount_received))
			for t in invoice.terms
			if flt(t.amount_received)
		]
	elif invoice:
		term.invoice_amount = flt(invoice.amount_invoiced) or term.invoice_amount
	elif term.status == "Paid" and not flt(term.amount_received):
		term.payments = [(term.billed_on, term.invoice_amount)]

	if not term.payments and flt(term.amount_received):
		paid_on = getdate(term.payment_received_date) if term.payment_received_date else term.billed_on
		term.payments = [(paid_on, flt(term.amount_received))]


def get_month_windows(from_date, to_date):
	"""Monthly windows covering the date range, clipped to the range at both ends."""
	windows = []
	month_start = get_first_day(from_date)
	while month_start <= to_date:
		windows.append((max(month_start, from_date), min(getdate(get_last_day(month_start)), to_date)))
		month_start = getdate(add_months(month_start, 1))
	return windows


def overlap_days(period_from, period_to, window_start, window_end):
	start, end = max(period_from, window_start), min(period_to, window_end)
	return (end - start).days + 1 if start <= end else 0


def new_totals():
	return {"pending_terms": 0, "billed_value": 0.0, "received": 0.0, "to_collect": 0.0, "monthly_value": 0.0}


def add_to_totals(target, row):
	for key in new_totals():
		target[key] += row[key]
