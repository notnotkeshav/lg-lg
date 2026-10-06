"""Weekly mandatory-information reminder (scheduled every Monday, 9 AM).

Every branch head (Region Branches.branch_head) gets one system notification and one email
listing the records of their branch(es) that still have mandatory information missing:
    * Active CRM Contracts - fields in CONTRACT_FIELDS, plus an empty billing schedule
    * all CRM Organizations (customers) - fields in CUSTOMER_FIELDS
A branch head with several branches gets them all in a single mail.
"""

import frappe
from frappe.utils import escape_html, get_url_to_form, getdate, today

SENDER = "notify.himsolutek@lgepartner.com"

CONTRACT_FIELDS = {
	"customer_hc": "Customer HC",
	"amc_type": "AMC Type",
	"deal_type": "Contract Type",
	"bill_ship_code": "Bill To Code",
	"amount": "Amount",
}
CUSTOMER_FIELDS = {
	"customer_hc": "Customer HC",
	"industry": "Vertical",
	"warranty_expiry_date": "Warranty Expiry Date",
}


def send_weekly_missing_info_reminders():
	for branch_head, reminder in get_missing_info_reminders().items():
		send_missing_info_reminder(branch_head, reminder)


def get_missing_info_reminders():
	"""Return {branch_head: {"contracts": [...], "customers": [...]}}, each row carrying
	`missing`, the labels of its empty mandatory fields."""
	contracts = frappe.db.sql(
		f"""
		SELECT c.name, c.customer_name AS customer, c.branch, {", ".join(f"c.{f}" for f in CONTRACT_FIELDS)},
			EXISTS(
				SELECT 1 FROM `tabContract Billing Schedule` b
				WHERE b.parent = c.name AND b.parenttype = 'CRM Contract'
			) AS has_billing_schedule
		FROM `tabCRM Contract` c
		WHERE c.custom_contract_status = 'Active' AND c.docstatus < 2
		ORDER BY c.branch, c.name
		""",
		as_dict=True,
	)
	customers = frappe.get_all(
		"CRM Organization",
		fields=["name", "organization_name AS customer", "branch", *CUSTOMER_FIELDS],
		order_by="branch, name",
	)

	branch_heads = dict(frappe.get_all("Region Branches", fields=["name", "branch_head"], as_list=True))
	reminders = {}
	for key, rows, fields, extra_check in (
		("contracts", contracts, CONTRACT_FIELDS, lambda r: [] if r.has_billing_schedule else ["Billing Schedule"]),
		("customers", customers, CUSTOMER_FIELDS, lambda _: []),
	):
		for row in rows:
			row.missing = [label for field, label in fields.items() if not row.get(field)] + extra_check(row)
			if not row.missing:
				continue
			branch_head = branch_heads.get(row.branch)
			if not branch_head:
				frappe.log_error(
					f"{key[:-1].title()} {row.name}: branch '{row.branch}' has no Branch Head, reminder skipped",
					"Missing Info Reminder",
				)
				continue
			reminders.setdefault(branch_head, {"contracts": [], "customers": []})[key].append(row)

	return reminders


def send_missing_info_reminder(branch_head, reminder):
	def table(doctype, rows):
		cell = "border:1px solid #ccc;padding:4px 8px"
		head = "".join(f"<th style='{cell}'>{h}</th>" for h in ("ID", "Customer", "Branch", "Missing Information"))
		body = "".join(
			f"<tr><td style='{cell}'><a href='{get_url_to_form(doctype, r.name)}'>{r.name}</a></td>"
			f"<td style='{cell}'>{escape_html(r.customer or '')}</td><td style='{cell}'>{r.branch}</td>"
			f"<td style='{cell}'>{', '.join(r.missing)}</td></tr>"
			for r in rows
		)
		return f"<table style='border-collapse:collapse'><tr>{head}</tr>{body}</table>"

	contracts, customers = reminder["contracts"], reminder["customers"]
	sections = []
	if contracts:
		sections.append(f"<p><b>Active AMC Contracts ({len(contracts)})</b></p>" + table("CRM Contract", contracts))
	if customers:
		sections.append(f"<p><b>Customers ({len(customers)})</b></p>" + table("CRM Organization", customers))

	title = f"[Action Required] Mandatory information missing – {len(contracts)} contracts, {len(customers)} customers"
	summary = (
		f"{len(contracts)} active AMC contract(s) and {len(customers)} customer(s) of your branch "
		f"have mandatory information missing. Please fill it in at the earliest."
	)

	frappe.get_doc({
		"doctype": "Notification Log",
		"type": "Alert",
		"for_user": branch_head,
		"subject": title,
		"email_content": summary,
	}).insert(ignore_permissions=True)

	try:
		frappe.sendmail(
			recipients=[frappe.db.get_value("User", branch_head, "email") or branch_head],
			sender=SENDER,
			subject=f"{title} ({getdate(today()).strftime('%d %b %Y')})",
			message=f"""
				<p>Hello,</p>
				<p>{summary}</p>
				{"<br>".join(sections)}
				<br>
				<p>Regards,<br>Hi-M Tech Solutek Pvt. Ltd.</p>
			""",
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Missing Info Reminder Email Error")
