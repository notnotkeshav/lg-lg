"""Warranty/AMC expiry follow-up (daily scheduled job).

The first notice goes out NOTICE_MONTHS before the Warranty/AMC expiry date, and the
responsibility for following up with the customer then escalates:
    0 - 1   month  -> AM  (contract user / opportunity owner, falls back to the branch head)
    1 - 1.5 months -> RSM (region head)
    1.5 months on  -> HO  (users with the HO_ROLE role)
LOST_AFTER_MONTHS after expiry, an opportunity whose customer is still not interested
is marked "Lost". This is the only rule that auto-marks a CRM Deal as Lost.

Followed up: AMC CRM Contracts, and Warranty CRM Deals linked to a Project.
At every stage each responsible user gets a CRM Task, a system notification and an email,
but only while that stage is less than STAGE_NOTICE_DAYS old - so missed runs are caught up,
while a backlog of stages that started long ago (e.g. when this job was introduced) is not.
"""

import frappe
from frappe.utils import add_days, add_months, formatdate, get_url_to_form, getdate, today

NOTICE_MONTHS = 2
LOST_AFTER_MONTHS = 3
HO_ROLE = "Alok"
STAGE_NOTICE_DAYS = 7
SENDER = "notify.himsolutek@lgepartner.com"

# Deal statuses that show the customer is engaged in the renewal, so the deal is never
# auto-marked as Lost. "Lost by AM" / "Lost by RSM" are deliberately not listed: a customer
# still not interested by the Lost date gets the deal finalized as Lost.
ENGAGED_DEAL_STATUSES = ["Proposal/Quotation", "Negotiation", "Spec-In", "Ready to Close", "Won/Award"]
NOT_LOSABLE_DEAL_STATUSES = ENGAGED_DEAL_STATUSES + ["Lost", "Sales"]
# Follow-up is over once the renewal is won or lost
CLOSED_DEAL_STATUSES = ["Won/Award", "Lost"]
INACTIVE_CONTRACT_STATUSES = ["Discontinue", "Rejected"]


def get_lost_date(expiry_date):
	return getdate(add_months(expiry_date, LOST_AFTER_MONTHS))


def get_follow_up_stage(expiry_date, on_date=None):
	"""Return (stage, stage_start_date, stage_end_date) for something expiring on
	expiry_date, where stage is None (not due yet), "AM", "RSM", "HO" or "Lost"."""
	expiry_date = getdate(expiry_date)
	on_date = getdate(on_date or today())

	notice_date = getdate(add_months(expiry_date, -NOTICE_MONTHS))
	rsm_date = getdate(add_months(notice_date, 1))
	ho_date = add_days(rsm_date, 15)
	lost_date = get_lost_date(expiry_date)

	if on_date < notice_date:
		return None, None, None
	if on_date < rsm_date:
		return "AM", notice_date, add_days(rsm_date, -1)
	if on_date < ho_date:
		return "RSM", rsm_date, add_days(ho_date, -1)
	if on_date < lost_date:
		return "HO", ho_date, add_days(lost_date, -1)
	return "Lost", lost_date, None


def run_expiry_follow_up():
	current_date = getdate(today())

	for subject in get_due_contracts(current_date) + get_due_warranty_deals(current_date):
		stage, stage_start, due_date = get_follow_up_stage(subject.expiry_date, current_date)
		if stage not in ("AM", "RSM", "HO"):
			continue
		if (current_date - stage_start).days >= STAGE_NOTICE_DAYS:
			continue

		try:
			follow_up(subject, stage, due_date)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				message=f"Failed to process expiry follow-up ({stage}) for {subject.doctype} {subject.name}:\n{frappe.get_traceback()}",
				title="Expiry Follow-up Error",
			)

	mark_not_interested_deals_lost(current_date)


def get_follow_up_window(current_date):
	# Expiry dates whose follow-up (notice -> Lost date) is running today
	return [add_months(current_date, -LOST_AFTER_MONTHS), add_months(current_date, NOTICE_MONTHS)]


def get_due_contracts(current_date):
	contracts = frappe.get_all(
		"CRM Contract",
		filters={
			"docstatus": ["<", 2],
			"custom_contract_status": ["not in", INACTIVE_CONTRACT_STATUSES],
			"expiry_date": ["between", get_follow_up_window(current_date)],
		},
		fields=["name", "customer", "customer_name", "project", "branch", "region", "user", "expiry_date"],
	)

	subjects = []
	for contract in contracts:
		# Renewal already won or lost - nobody needs to follow up any more
		if frappe.db.exists("CRM Deal", {"from_contract": contract.name, "status": ["in", CLOSED_DEAL_STATUSES]}):
			continue

		subjects.append(frappe._dict(
			doctype="CRM Contract",
			name=contract.name,
			label="AMC contract",
			customer=contract.customer_name or contract.customer,
			project=contract.project,
			expiry_date=contract.expiry_date,
			am_user=contract.user,
			branch=contract.branch,
			region=contract.region,
		))
	return subjects


def get_due_warranty_deals(current_date):
	deals = frappe.get_all(
		"CRM Deal",
		filters=[
			["warranty_expiry_date", "between", get_follow_up_window(current_date)],
			["amc_expiry_date", "is", "not set"],
			["project", "is", "set"],
			["status", "not in", CLOSED_DEAL_STATUSES],
		],
		fields=["name", "customer", "project", "branch", "region", "deal_owner", "warranty_expiry_date"],
	)

	subjects = []
	for deal in deals:
		# Warranty already converted to an AMC - the contract is followed up instead
		if frappe.db.exists("CRM Contract", {"from_deal": deal.name, "docstatus": ["<", 2]}):
			continue

		subjects.append(frappe._dict(
			doctype="CRM Deal",
			name=deal.name,
			label="Warranty opportunity",
			customer=deal.customer,
			project=deal.project,
			expiry_date=deal.warranty_expiry_date,
			am_user=deal.deal_owner,
			branch=deal.branch,
			region=deal.region,
		))
	return subjects


def get_follow_up_users(subject, stage):
	if stage == "AM":
		user = subject.am_user
		if not user and subject.branch:
			user = frappe.db.get_value("Region Branches", subject.branch, "branch_head")
		return [user] if user else []

	if stage == "RSM":
		region = subject.region
		if not region and subject.branch:
			region = frappe.db.get_value("Region Branches", subject.branch, "region")
		user = region and frappe.db.get_value("Region Master", region, "region_head")
		return [user] if user else []

	if stage == "HO":
		return frappe.db.sql_list(
			"""
			SELECT DISTINCT hr.parent
			FROM `tabHas Role` hr
			JOIN `tabUser` u ON u.name = hr.parent
			WHERE hr.role = %s AND hr.parenttype = 'User' AND u.enabled = 1
				AND u.name NOT IN ('Administrator', 'Guest')
			""",
			HO_ROLE,
		)

	return []


def follow_up(subject, stage, due_date):
	users = get_follow_up_users(subject, stage)
	if not users:
		frappe.log_error(
			message=f"No {stage} user found for {subject.doctype} {subject.name} (branch: {subject.branch}, region: {subject.region})",
			title="Expiry Follow-up - No Assignee",
		)
		return

	title = f"Expiry Follow-up ({stage}) - {subject.name}"
	message = get_follow_up_message(subject, stage, due_date)

	for user in users:
		# One task and notification per document, stage and user - the job runs daily
		if frappe.db.exists(
			"CRM Task",
			{
				"reference_doctype": subject.doctype,
				"reference_docname": subject.name,
				"title": title,
				"assigned_to": user,
			},
		):
			continue

		frappe.get_doc({
			"doctype": "CRM Task",
			"title": title,
			"reference_doctype": subject.doctype,
			"reference_docname": subject.name,
			"description": message,
			"assigned_to": user,
			"priority": "High",
			"status": "Todo",
			"start_date": today(),
			"due_date": due_date,
		}).insert(ignore_permissions=True)

		notify(user, subject, title, message)


def get_follow_up_message(subject, stage, due_date):
	days_left = (getdate(subject.expiry_date) - getdate(today())).days
	expiry_text = formatdate(subject.expiry_date)
	if days_left >= 0:
		expiry_text += f" ({days_left} days left)"
	else:
		expiry_text += f" (expired {-days_left} days ago)"

	lost_text = (
		f"If the customer is not interested, the opportunity will be marked as Lost on "
		f"{formatdate(get_lost_date(subject.expiry_date))}, {LOST_AFTER_MONTHS} months after expiry."
	)
	next_step = {
		"AM": f"After that, it will be escalated to RSM. {lost_text}",
		"RSM": f"After that, it will be escalated to HO. {lost_text}",
		"HO": lost_text,
	}[stage]

	link = f"<a href='{get_url_to_form(subject.doctype, subject.name)}'>{subject.name}</a>"
	project = f" (Project {subject.project})" if subject.project else ""
	return (
		f"Warranty/AMC of {subject.label} {link} for customer {subject.customer or ''}{project} "
		f"expires on {expiry_text}.<br>"
		f"You are responsible for following up with the customer for renewal "
		f"until {formatdate(due_date)}. {next_step}"
	)


def notify(user, subject, title, message):
	frappe.get_doc({
		"doctype": "Notification Log",
		"type": "Alert",
		"for_user": user,
		"document_type": subject.doctype,
		"document_name": subject.name,
		"subject": title,
		"email_content": message,
	}).insert(ignore_permissions=True)

	try:
		frappe.sendmail(
			recipients=[frappe.db.get_value("User", user, "email") or user],
			sender=SENDER,
			subject=title,
			message=f"<p>Hello,</p><p>{message}</p><p>Regards,<br>Hi-M Tech Solutek Pvt. Ltd.</p>",
			reference_doctype=subject.doctype,
			reference_name=subject.name,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Expiry Follow-up Email Error")


def mark_not_interested_deals_lost(current_date):
	"""Mark a Deal "Lost" once LOST_AFTER_MONTHS have passed since the Warranty/AMC expiry
	of the deal itself or of the contract it renews, unless the customer is engaged."""
	rows = frappe.db.sql(
		"""
		SELECT d.name, IFNULL(d.amc_expiry_date, d.warranty_expiry_date) AS expiry_date, NULL AS contract
		FROM `tabCRM Deal` d
		WHERE d.status NOT IN %(not_losable)s
			AND IFNULL(d.amc_expiry_date, d.warranty_expiry_date) < %(today)s
		UNION ALL
		SELECT d.name, c.expiry_date, c.name AS contract
		FROM `tabCRM Contract` c
		JOIN `tabCRM Deal` d ON d.from_contract = c.name OR d.name = c.from_deal
		WHERE c.docstatus < 2
			AND IFNULL(c.custom_contract_status, '') NOT IN %(inactive)s
			AND c.expiry_date < %(today)s
			AND d.status NOT IN %(not_losable)s
		""",
		{
			"not_losable": NOT_LOSABLE_DEAL_STATUSES,
			"inactive": INACTIVE_CONTRACT_STATUSES,
			"today": current_date,
		},
		as_dict=True,
	)

	# A deal can renew a contract and carry its own expiry - go by the latest one
	latest = {}
	for row in rows:
		if row.name not in latest or getdate(row.expiry_date) > getdate(latest[row.name].expiry_date):
			latest[row.name] = row

	for row in latest.values():
		if get_lost_date(row.expiry_date) > current_date:
			continue

		try:
			mark_deal_lost(row.name, row.expiry_date, row.contract)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				message=f"Failed to mark CRM Deal {row.name} as Lost:\n{frappe.get_traceback()}",
				title="Expiry Follow-up Error",
			)


def mark_deal_lost(deal_name, expiry_date, contract=None):
	deal = frappe.get_doc("CRM Deal", deal_name)
	if not deal.reason:
		expired = f"contract {contract}" if contract else "Warranty/AMC"
		deal.reason = (
			deal.lost_by_rsm
			or deal.lost_by_am
			or f"Customer not interested in renewal within {LOST_AFTER_MONTHS} months of "
			f"{expired} expiry on {formatdate(expiry_date)}"
		)
	deal.status = "Lost"
	deal.flags.ignore_mandatory = True
	deal.save(ignore_permissions=True)
