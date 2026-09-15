# Copyright (c) 2024, extension and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime
from frappe import _
from dateutil.relativedelta import relativedelta
from frappe.model.document import Document
from frappe.utils import (
	add_months,
	get_first_day,
	get_last_day,
	nowdate,
	getdate,
	flt,
	today,
	add_days,
	date_diff,
	cint
)
from frappe.utils.formatters import fmt_money
import json
from datetime import datetime
import pandas as pd


class CRMQuotation(Document):
	def validate(self):
		if not self.customer:
			frappe.throw(_("Customer is required"))

		self.set_amc_duration()
		self.set_multi_year_details()

	def get_print_format(self):
		"""Multi year quotations print year wise."""
		return "AMC Offer Quote Multi Year" if self.is_multi_year else "AMC Offer quote"

	def set_amc_duration(self):
		"""Derive AMC Term (in Years) and AMC Term (in Months) from Start / End Date."""
		if not (self.start_date and self.end_date):
			return

		start, end = getdate(self.start_date), getdate(self.end_date)
		if start > end:
			frappe.throw(_("End Date must be after Start Date"))

		self.amc_term = get_amc_months(start, end)
		self.amc_year = self.amc_term // 12

	def get_yearly_amounts(self):
		"""Per-year charges held in price_rate__as_per_year.

		The field is a comma separated list covering year 2 onward: the first
		value is year 2's total charge, the second year 3's, and so on. It is an
		amount, not a per-HP rate. Year 1 is always total_hp * price_rate.
		"""
		amounts = []
		for part in (self.price_rate__as_per_year or "").split(","):
			part = part.strip()
			if not part:
				continue
			try:
				amounts.append(flt(part))
			except (TypeError, ValueError):
				continue
		return amounts

	def get_amount_for_year(self, year_no, months=12):
		"""Charge for a 1-based contract year, prorated when the year is partial."""
		if cint(year_no) <= 1:
			annual = flt(self.total_hp) * flt(self.price_rate)
		else:
			amounts = self.get_yearly_amounts()
			if amounts:
				# if fewer values than years are given, carry the last one forward
				annual = amounts[min(cint(year_no) - 2, len(amounts) - 1)]
			else:
				annual = flt(self.total_hp) * flt(self.price_rate)

		return annual * cint(months) / 12.0

	def get_rate_for_year(self, year_no):
		"""Per-HP rate implied by that year's charge. Year 1 is price_rate itself."""
		if cint(year_no) <= 1:
			return flt(self.price_rate)

		hp = flt(self.total_hp)
		return self.get_amount_for_year(year_no, 12) / hp if hp else 0.0

	def get_year_breakup(self):
		"""Year wise rows, computed from the current field values.

		Print formats call this directly rather than reading amc_yearly_breakup,
		so a quotation saved before the pricing changed still prints correctly.
		rate_per_hp and amount are always derived - never carried forward.
		"""
		months = cint(self.amc_term)
		if not months or not self.start_date:
			return []

		rows = []
		start = getdate(self.start_date)
		year_no = 1
		remaining = months

		while remaining > 0:
			span = min(12, remaining)
			from_date = add_months(start, (year_no - 1) * 12)
			to_date = add_days(add_months(from_date, span), -1)
			if self.end_date and getdate(to_date) > getdate(self.end_date):
				to_date = getdate(self.end_date)

			rows.append({
				"year_no": year_no,
				"year_label": _("Year {0}").format(year_no),
				"from_date": from_date,
				"to_date": to_date,
				"months": span,
				"rate_per_hp": self.get_rate_for_year(year_no),
				"amount": self.get_amount_for_year(year_no, span),
			})

			remaining -= span
			year_no += 1

		return rows

	def set_multi_year_details(self):
		"""Auto detect a multi year quotation and build its year wise breakup."""
		months = cint(self.amc_term)
		self.is_multi_year = 1 if (months > 12 or cint(self.amc_year) > 1) else 0

		if not self.is_multi_year or not self.start_date:
			self.amc_yearly_breakup = []
			return

		self.amc_yearly_breakup = []
		for row in self.get_year_breakup():
			self.append("amc_yearly_breakup", row)

		# the quotation total has to match the year wise rows, otherwise the
		# billing schedule and the taxes are computed off a different figure
		self.amount = sum(flt(row.amount) for row in self.amc_yearly_breakup)


def get_amc_months(start, end):
	"""Inclusive month count between two dates, e.g. 01-Jan-25 to 31-Dec-26 = 24."""
	start, end = getdate(start), getdate(end)
	if end < start:
		return 0

	# end date is inclusive, so measure up to the day after it
	delta = relativedelta(add_days(end, 1), start)
	months = delta.years * 12 + delta.months

	# any leftover days count as a further (part) month
	if delta.days > 0:
		months += 1

	return months

	def on_update(self,method=None):
		if self.workflow_state == "Customer Approval Pending" and self.customer:

			# Customer email fetch
			email = frappe.db.get_value("CRM Organization", self.customer, "email")

			if not email:
				frappe.msgprint("Customer email not found")
				return

			# Attach print format PDF
			attachment = frappe.attach_print(
				self.doctype,
				self.name,
				file_name=self.name,
				print_format=self.get_print_format(),
				lang="en"
			)

			frappe.sendmail(
                sender="econnect.himsolutek@lgepartner.com",
				recipients=[email],
				subject=f"Quotation {self.name}",
				message="Please find attached quotation.",
				attachments=[attachment],
				reference_doctype=self.doctype,
				reference_name=self.name
			)
				
@frappe.whitelist()
def create_quotation(args):
	"""Create a new quotation"""
	try:
		args = frappe.parse_json(args)
		doc = frappe.new_doc('CRM Quotation')
		doc.update(args)
		doc.insert()
		return doc
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), _('Quotation Creation Failed'))
		frappe.throw(_('Could not create quotation: {0}').format(str(e)))

@frappe.whitelist()
def get_fields_layout(name=None):
	"""Get the fields layout for the quotation form"""
	fields_to_exclude = ['naming_series', 'amended_from', 'owner', 'creation', 'modified', 'modified_by']
	
	meta = frappe.get_meta('CRM Quotation')
	fields = [f for f in meta.fields if f.fieldname not in fields_to_exclude]
	
	sections = [
		{
			"label": _("Organization Details"),
			"fields": [f for f in fields if f.fieldtype in ['Link', 'Data'] and f.fieldname in ['customer', 'customer_hc']]
		},
		{
			"label": _("Quotation Details"),
			"fields": [f for f in fields if f.fieldname in ['date', 'valid_till', 'status']]
		},
		{
			"label": _("Product Information"),
			"fields": [f for f in fields if f.fieldname in ['deal_type', 'serial_no', 'product_name']]
		},
		{
			"label": _("Pricing Details"),
			"fields": [f for f in fields if f.fieldname in ['amc', 'payment_frequency', 'currency', 'amount']]
		}
	]
	
	if name:
		doc = frappe.get_doc('CRM Quotation', name)
		for section in sections:
			for field in section['fields']:
				field.value = doc.get(field.fieldname)
	
	return sections

@frappe.whitelist()
def update_field_layout(fieldname, key, value):
	"""Update field layout settings"""
	if not frappe.has_permission("CRM Quotation", "write"):
		frappe.throw(_("Not allowed to update field layout"), frappe.PermissionError)
		
	docfield = frappe.get_doc("DocField", {
		"parent": "CRM Quotation",
		"fieldname": fieldname
	})
	
	if key in ["in_list_view", "reqd", "hidden"]:
		docfield.set(key, value)
		docfield.save(ignore_permissions=True)
		
	return True




@frappe.whitelist()
def get_quotation_metrics():
	"""Get metrics for quotations dashboard"""
	try:
		# Get status-wise counts
		status_counts = frappe.db.sql("""
			SELECT 
				status,
				COUNT(*) as count,
				COALESCE(SUM(amount), 0) as total_value
			FROM `tabCRM Quotation`
			GROUP BY status
		""", as_dict=True)

		# Calculate total value and count
		total_value = sum(item.get('total_value', 0) for item in status_counts)
		total_count = sum(item.get('count', 0) for item in status_counts)

		# Calculate growth for each status
		last_month = frappe.utils.add_months(frappe.utils.today(), -1)
		
		previous_status_counts = frappe.db.sql("""
			SELECT 
				status,
				COUNT(*) as count,
				COALESCE(SUM(amount), 0) as total_value
			FROM `tabCRM Quotation`
			WHERE creation <= %s
			GROUP BY status
		""", last_month, as_dict=True)

		# Create a map of previous counts
		prev_counts = {item.status: item.count for item in previous_status_counts}
		
		# Calculate growth for each status
		for item in status_counts:
			prev_count = prev_counts.get(item.status, 0)
			if prev_count > 0:
				item['growth'] = ((item.count - prev_count) / prev_count) * 100
			else:
				item['growth'] = 100 if item.count > 0 else 0

		# Get trend data for visualization
		trend_data = frappe.db.sql("""
			SELECT 
				DATE_FORMAT(creation, '%Y-%m') as month,
				status,
				COUNT(*) as count
			FROM `tabCRM Quotation`
			WHERE creation >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
			GROUP BY DATE_FORMAT(creation, '%Y-%m'), status
			ORDER BY month ASC
		""", as_dict=True)

		return {
			"status_counts": status_counts,
			"total_value": total_value,
			"total_count": total_count,
			"trend_data": trend_data
		}
	
	except Exception as e:
		frappe.log_error(f"Could not calculate quotation metrics: {str(e)}")
		return {
			"status_counts": [],
			"total_value": 0,
			"total_count": 0,
			"trend_data": []
		}

@frappe.whitelist()
def export_report(filters=None):
	"""Export quotation report data"""
	try:
		if isinstance(filters, str):
			filters = json.loads(filters)

		# Get metrics data
		metrics = get_quotation_metrics()
		
		# Create Excel writer
		from frappe.utils.xlsxutils import make_xlsx
		
		# Prepare data for different sheets
		xlsx_data = {
			"Summary": [
				["Metric", "Value", "Change"],
				["Total Quotation Value", metrics["total_value"], f"{metrics['growth']}%"],
				["Total Quotations", metrics["total_count"], f"{metrics['growth']}%"]
			]
		}
		
		# Generate Excel file
		xlsx_file = make_xlsx(xlsx_data, "CRM Quotation")
		
		# Save file and get URL
		file_url = frappe.utils.get_site_path('private', 'files', 'quotation_report.xlsx')
		with open(file_url, 'wb') as f:
			f.write(xlsx_file.getvalue())
			
		return {
			"file_url": file_url
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), _('Quotation Report Export Failed'))
		frappe.throw(_('Could not export report: {0}').format(str(e)))



def hp_in_range(hp_value, hp_str):
    if not hp_str:
        return False

    s = hp_str.upper().replace("HP", "").strip().replace(" ", "")

    # Handle "~300"
    if s.startswith("~"):
        try:
            max_hp = float(s[1:])
            return hp_value <= max_hp
        except:
            return False

    # Handle "100~300" or "100-300"
    if "~" in s:
        parts = s.split("~")
    elif "-" in s:
        parts = s.split("-")
    else:
        try:
            return float(s) == hp_value
        except:
            return False

    if len(parts) == 2:
        try:
            min_hp = float(parts[0])
            max_hp = float(parts[1])
            return min_hp <= hp_value <= max_hp
        except:
            return False

    return False



@frappe.whitelist()
def get_zone_from_vertical_master(horse_power, project_type=None, start_date=None, end_date=None, price_rate=None):
    if not project_type:
        return {"error": "Industry (Project Type) is required."}

    industry_doc = frappe.db.get_value("CRM Industry", project_type, "parent_vertical", as_dict=True)
    if not industry_doc or not industry_doc.parent_vertical:
        return {"error": "No Parent Vertical linked for this Industry."}

    parent_vertical = industry_doc.parent_vertical

    # Now fetch Vertical Master using parent_vertical
    vertical_doc = frappe.get_doc("Vertical Master", parent_vertical)


    # Calculate AMC Year and Term
    amc_year, amc_term = 0, 0
    try:
        if start_date and end_date:
            if getdate(end_date) < getdate(start_date):
                return {"error": "Start Date cannot be after End Date."}

            amc_term = get_amc_months(start_date, end_date)
            amc_year = amc_term // 12
    except Exception as e:
        return {"error": f"Invalid date format or date error: {e}"}

    # Parse HP
    try:
        hp = float(horse_power)
    except:
        return {"error": "Invalid HP value"}

    # Parse price_rate
    try:
        price_rate = float(price_rate) if price_rate else None
    except:
        price_rate = None

    matched_zone = None
    matched_price = None
    matched_min = None
    matched_max = None

    # Find matching zone from Vertical Master
    for row in vertical_doc.hp_and_zone_details:
        try:
            if not row.hp or not row.zone:
                continue

            hp_range = row.hp.replace("HP", "").replace("\u2013", "~").replace("\u2014", "~").replace("-", "~").strip()
            zone = row.zone
            min_rate = float(row.minimum_rate or 0)
            max_rate = float(row.maximum_rate or 0)

            hp_match = False
            if "~" in hp_range:
                hp_from, hp_to = map(float, hp_range.split("~"))
                if hp_from <= hp <= hp_to:
                    hp_match = True
            elif float(hp_range) == hp:
                hp_match = True

            if hp_match:
                if price_rate is None or (min_rate <= price_rate <= max_rate):
                    matched_zone = zone
                    matched_price = max_rate
                    matched_min = min_rate
                    matched_max = max_rate
                    break
                elif not matched_zone:
                    matched_zone = zone
                    matched_price = max_rate
                    matched_min = min_rate
                    matched_max = max_rate
        except Exception as e:
            frappe.log_error(f"Error parsing HP range '{row.hp}': {e}", "CRM Quotation: get_zone_from_vertical_master")

    if not matched_zone:
        return {"error": "No matching zone found for the given HP."}

    return {
        "zone": matched_zone,
        "amc_year": amc_year,
        "amc_term": amc_term,
        "price_rate": matched_price,
        "minimum_rate": matched_min,
        "maximum_rate": matched_max
    }


# def check_advance_payment_reminders():
#     today = getdate(nowdate())

#     contracts = frappe.get_all("CRM Quotation", filters={"docstatus": 0}, fields=["name", "advance_amount", "customer", "owner", "advance_end_date","is_govt"])

#     for contract in contracts:
#         if not contract.advance_amount:
#             continue

#         doc = frappe.get_doc("CRM Quotation", contract.name)

#         # Make sure billing schedule exists
#         if not doc.billing_schedule or len(doc.billing_schedule) == 0:
#             continue

#         first_row = doc.billing_schedule[0]

#         # Check if first row is advance, pending, and overdue
#         if (
#             first_row.is_advance == 1
#             and first_row.status.lower() == "pending"
#             and doc.advance_end_date
#             and doc.advance_end_date <= today
#         ):
#             days_due = date_diff(today, doc.advance_end_date)

#             # ✅ Fetch is_govt from linked Customer (0 or 1)
#             is_govt = doc.is_govt

#             # ✅ Send reminders based on days and is_govt
#             if (is_govt == 0 and days_due in [1,20, 25, 30]) or \
#                (is_govt == 1 and days_due in [1,20, 25, 30, 60]):

#                 send_advance_reminder(contract.name, doc.owner, days_due, doc.advance_end_date)

#                 if (is_govt == 0 and days_due >= 30) or \
#                    (is_govt == 1 and days_due >= 60):
#                     mark_or_notify_discontinuation(doc)

@frappe.whitelist()
def check_advance_payment_reminders():
    today = getdate(nowdate())

    quotations = frappe.get_all(
        "CRM Quotation",
        filters={"docstatus": 0},
        fields=["name", "advance_amount", "customer", "owner", "advance_end_date", "is_govt"]
    )

    for q in quotations:
        if not q.advance_amount:
            continue

        doc = frappe.get_doc("CRM Quotation", q.name)

        # Filter only unpaid rows having payment_date, sort by payment_date
        unpaid_rows = sorted(
            [row for row in doc.billing_schedule if row.status.lower() != "Paid" and row.payment_date],
            key=lambda x: x.payment_date
        )

        if not unpaid_rows:
            continue

        # Take the earliest unpaid row
        first_due_row = unpaid_rows[0]
        days_due = date_diff(today, first_due_row.payment_date)

        # Govt or non-govt reminder logic
        if (days_due in [1, 20, 25, 30]) or \
           (days_due in [1, 20, 25, 30, 60]):

            send_advance_reminder(doc.name, doc.owner, days_due, first_due_row.payment_date)

        # Discontinuation check
        if (days_due >= 60):

            mark_or_notify_discontinuation(doc)

from frappe import _

def send_advance_reminder(contract_name, owner, days_due, advance_end_date):
    print(f"📧 Triggering email reminder for: {contract_name}, Owner: {owner}, Days Due: {days_due}, Due Date: {advance_end_date}")

    if not owner:
        msg = f"⚠️ No owner assigned for contract {contract_name}, cannot send reminder."
        print(msg)
        frappe.log_error(title="Advance Reminder Error", message=msg)
        return msg
    owner_email = frappe.db.get_value("User", owner, "email") or owner

    subject = f"[Reminder] Advance Payment Overdue by {days_due} Days"
    message = f"""
        <p>Hello,</p>
        <p>The advance payment for contract <b>{contract_name}</b> was due on <b>{advance_end_date}</b>.</p>
        <p>It has now been overdue by <b>{days_due} days</b> and is still <span style="color:red">unpaid</span>.</p>
        <p>Please take immediate action.</p>
        <br>
        <p>Regards,<br>Hi-M Solutek Pvt. Ltd.</p>
    """

    try:
        frappe.sendmail(
            recipients=[owner_email],
            sender="notify.himsolutek@lgepartner.com",
            subject=subject,
            message=message,
            reference_doctype="CRM Contract",
            reference_name=contract_name
        )
        log_msg = f"✅ Email reminder sent to {owner} for contract {contract_name}"
        print(log_msg)
        return log_msg

    except Exception:
        error_msg = f"❗ Failed to send email reminder for {contract_name} to {owner}"
        print(error_msg)
        frappe.log_error(title="Failed to Send Email Reminder", message=frappe.get_traceback())
        return error_msg


def mark_or_notify_discontinuation(doc):
    today = frappe.utils.nowdate()
    # Log and optionally mark as Discontinued
    frappe.log_error(f"Advance not received for Contract: {doc.name}")

    if doc.custom_contract_status != "Discontinue":
        frappe.db.set_value("CRM Contract", doc.name, {
            "custom_contract_status": "Discontinue",
            "discontinue_date": today
        })
        frappe.db.commit()


import frappe

@frappe.whitelist()
def send_zone_approval_alert_api(docname, doctype="CRM Quotation"):
    """
    Trigger zone approval email + notification log based on workflow_state of the doc
    """
    try:
        doc = frappe.get_doc(doctype, docname)

        # Mapping workflow state to role
        state_role_map = {
            "Orange Zone Approval Pending": "Orange Zone Approver",
            "Yellow Zone Approval Pending": "Yellow Zone Approver",
            "Red Zone Approval Pending": "Red Zone Approver"
        }

        role = state_role_map.get(doc.workflow_state)
        if not role:
            frappe.log_error(f"Workflow state '{doc.workflow_state}' not in zone list", "Zone Approval Notification")
            return {"status": "no_action", "message": "Workflow state not in zone list"}

        # Get all users who have this role (except Administrator)
        recipients = frappe.get_all(
            "Has Role",
            filters={"role": role},
            fields=["parent"]
        )
        user_emails = [u["parent"] for u in recipients if u["parent"] != "Administrator"]

        if not user_emails:
            frappe.log_error(f"No recipients found for role: {role}", "Zone Approval Notification")
            return {"status": "error", "message": "No recipients found"}

        # Create Notification Log entries
        for user in user_emails:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"{doc.doctype} {doc.name} requires your approval",
                "for_user": user,
                "type": "Alert",
                "email_content": f"""
                    <p>{doc.doctype} <b>{doc.name}</b> is currently in <b>{doc.workflow_state}</b> state.</p>
                    <p>Please review and take necessary action.</p>
                """,
                "document_type": doc.doctype,
                "document_name": doc.name
            }).insert(ignore_permissions=True)


        frappe.sendmail(
            recipients=user_emails,
            sender="notify.himsolutek@lgepartner.com",
            subject=f"{doc.workflow_state} - Action Required",
            message=f"""
                <p>Dear Approver,</p>
                <p>{doc.doctype} <b>{doc.name}</b> is currently in <b>{doc.workflow_state}</b> state.</p>
                <p>Please review and take necessary action.</p>
            """
        )

        return {"status": "success", "recipients": user_emails}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Zone Approval Alert Error")
        return {"status": "error", "message": str(e)}


# @frappe.whitelist()
# def send_billing_schedule_email(quote_name):
#     quote = frappe.get_doc("CRM Quotation", quote_name)
    
#     # Compose email content
#     customer_name = quote.customer
#     project = quote.project
#     opportunity = quote.deal
#     days = quote.days
#     email_to = quote.contact_email
   
#     # Build table HTML
#     table_html = """
#     <table border="1" cellpadding="5" cellspacing="0">
#         <tr>
#             <th>Billing Terms</th>
#             <th>Status</th>
#             <th>Billing Date</th>
#             <th>Payment Date</th>
#             <th>Amount</th>
#         </tr>
#     """
#     for row in quote.billing_schedule:
#         table_html += f"""
#         <tr>
#             <td>{row.billing_term}</td>
#             <td>{row.status}</td>
#             <td>{row.billing_date}</td>
#             <td>{row.payment_date}</td>
#             <td>{row.amount}</td>
#         </tr>
#         """
#     table_html += "</table>"
#     message = f"""
#         <p>Dear Customer,</p>

#         <p>We would like to inform you that the <strong>Billing Schedule</strong> has been created/updated for your quotation.</p>

#         <p><strong>Details:</strong></p>
#         <ul>
#             <li><strong>Customer:</strong> {customer_name}</li>
#             <li><strong>Project:</strong> {project}</li>
#             <li><strong>Opportunity:</strong> {opportunity}</li>
#             <li><strong>Payment Terms:</strong> Advance with {days} Credit Days</li>
#         </ul>

#         <p><strong>Billing Schedule:</strong></p>
#         {table_html}

#         <p style="margin-top:15px;">
#             Please review the schedule above. For any queries or clarifications, feel free to contact our team.
#         </p>

        
#         """


#     frappe.sendmail(
#         recipients=[email_to],
#         sender="noreply@lgepartner.com",
#         subject=f"Updated Billing Schedule for {customer_name} - Quotation {quote_name}",
#         message=message,
#         reference_doctype="CRM Contract",
#         reference_name=quote_name
#     )



@frappe.whitelist()
def update_workflow_to_sent(docname):
	"""
	Update workflow state from Approved to Quote Sent to Customer
	Uses direct SQL update to bypass all validations
	"""
	try:
		# First verify the document exists and is in Approved state
		current_state = frappe.db.get_value("CRM Quotation", docname, "workflow_state")
		
		if current_state != "Approved":
			return {
				"success": False,
				"message": f"Document must be in 'Approved' state. Current: {current_state}"
			}
		
		# Direct SQL update - bypasses all validations including status field validation
		frappe.db.sql("""
			UPDATE `tabCRM Quotation`
			SET workflow_state = %s,
				modified = %s,
				modified_by = %s
			WHERE name = %s
		""", ("Customer Approval Pending", frappe.utils.now(), frappe.session.user, docname))
		
		# Commit the transaction
		frappe.db.commit()
		
		# Verify the update
		new_state = frappe.db.get_value("CRM Quotation", docname, "workflow_state")
		
		# Add a comment for tracking
		doc = frappe.get_doc("CRM Quotation", docname)
		doc.add_comment(
			"Workflow",
			f"Workflow state changed from 'Approved' to 'Quote Sent to Customer' - Quote sent to customer"
		)
		
		return {
			"success": True,
			"message": f"Workflow updated successfully",
			"new_state": new_state
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Update Workflow Error")
		return {
			"success": False,
			"message": f"Error: {str(e)}"
		}