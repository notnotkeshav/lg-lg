# Copyright (c) 2024, extension and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, add_months, date_diff,today,add_days, flt, fmt_money, formatdate, get_first_day
import json
import re
import datetime
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.model.mapper import get_mapped_doc
from frappe.utils import now_datetime,getdate,nowdate

from lg.api.exchange_rate import get_exchange_rate
from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import add_status_change_log
from dateutil.relativedelta import relativedelta


class CRMContract(Document):
	def on_trash(self):
		# Unlink from Customer (CRM Organization) so Frappe's link check doesn't block deletion
		frappe.db.delete("Customer Contracts", {"contract_id": self.name})

	def on_submit(self):
		self.schedule_renewal_deal()
		self.update_serial_no()
		self.set_hp_in_deal_and_expiry_date()
		self.send_work_order_to_dealers()
		# self.fill_expiry_date_in_deal()

	
	def schedule_renewal_deal(self):
		"""Schedule creation of renewal deal 6 months before contract expiry"""
		if not self.expiry_date:
			return
			
		renewal_date = add_months(getdate(self.expiry_date), -6)
		today = getdate(now_datetime())
		
		# Check if we need to create a renewal deal
		if today >= renewal_date:
			self.create_renewal_deal()
	
	def create_renewal_deal(self):
		"""Create a renewal deal for this contract"""
		# Create new CRM Deal document
		deal = frappe.new_doc("CRM Deal")
		# Set required fields as per CRM Deal JSON schema
		deal.naming_series = "CRM-DEAL-.YYYY.-"
		deal.status = "Qualification"
		deal.from_contract = self.name
		deal.customer = self.customer
		deal.customer_name = self.customer
		deal.customer_hc = self.customer_hc
		deal.organization = self.company
		deal.serial_no = self.serial_no
		deal.product_name = self.product_name
		deal.expiry_date = self.expiry_date
		deal.start_date = self.start_date
		deal.deal_type = self.deal_type
		deal.insert()
		frappe.db.commit()
		# Insert the document
		# deal.insert(ignore_permissions=True)
		# frappe.msgprint(f"Renewal deal created for contract {self.name}")
		# frappe.db.commit()

		deal = frappe.get_doc({
		"doctype": "CRM Deal",
		"name": deal.name,
		})
		# deal.insert(ignore_permissions=True)
		name = deal.name
		path = frappe.utils.get_url('/app/form/CRM Deal/' + name)
		msg = f"Renewal deal created for contract {self.name} against the customer {self.customer}. The link for the deal created is <a href='{path}' target='_blank'>{name}</a>"
		frappe.msgprint(msg)
		frappe.db.commit()
	
	


	def update_serial_no(self):
		"""Update Serial No document with contract dates and calculations"""
		if not self.serial_no:
			return

		today = getdate(now_datetime())
		start_date = getdate(self.start_date) if self.start_date else None
		expiry_date = getdate(self.expiry_date) if self.expiry_date else None

		update_fields = {
			'start_date': self.start_date,
			'expiry_date': self.expiry_date
		}

		# Calculate warranty period in days
		if start_date and expiry_date:
			warranty_period = date_diff(expiry_date, start_date)
			if warranty_period >= 0:
				update_fields['warranty_period_in_days'] = warranty_period
			else:
				frappe.msgprint("Expiry Date should be after Start Date")
				update_fields['warranty_period_in_days'] = 0

		# Calculate days left
		if expiry_date:
			days_left = date_diff(expiry_date, today)
			if days_left >= 0:
				update_fields['days_left'] = days_left
			else:
				frappe.msgprint("The expiry date has already passed.")
				update_fields['days_left'] = 0

		# Update Serial No
		frappe.db.set_value(
			'Serial No',
			self.serial_no,
			update_fields,
			update_modified=False
		)



class CRMContract(Document):
		@staticmethod
		def default_list_data():
			columns = [
				{
					'label': 'Contract',
					'type': 'Data',
					'key': 'organization_name',
					'width': '16rem',
				},
				{
					'label': 'Website',
					'type': 'Data',
					'key': 'website',
					'width': '14rem',
				},
				{
					'label': 'Industry',
					'type': 'Link',
					'key': 'industry',
					'options': 'CRM Industry',
					'width': '14rem',
				},
				{
					'label': 'Annual Revenue',
					'type': 'Currency',
					'key': 'annual_revenue',
					'width': '14rem',
				},
				{
					'label': 'Last Modified',
					'type': 'Datetime',
					'key': 'modified',
					'width': '8rem',
				},
			]
			rows = [
				"name",
				"organization_name",
				"organization_logo",
				"website",
				"industry",
				"currency",
				"annual_revenue",
				"modified",
			]
			return {'columns': columns, 'rows': rows}


class CRMContract(Document):

	def on_update_after_submit(self):
		frappe.log_error("===== on_update_after_submit CALLED =====", "DEBUG")

		try:
			if hasattr(self, "_doc_before_save") and self._doc_before_save:
				old_doc = self._doc_before_save

				# loop over current rows
				for row in self.dealer:
					# find the matching row from old_doc
					old_row = next((r for r in old_doc.dealer if r.dealer_id == row.dealer_id), None)
					if old_row:
						old_value = old_row.commission_rate
						new_value = row.commission_rate

						frappe.log_error(f"Dealer {row.dealer_id} → Old: {old_value}, New: {new_value}", "Commission Update Debug")

						if new_value != old_value:
							frappe.log_error(f"Commission changed for dealer {row.dealer_id}, sending email...", "Commission Update Debug")
							self.send_commission_update_email(row, new_value)
					else:
						frappe.log_error(f"No old row found for dealer {row.dealer_id}", "Commission Update Debug")

		except Exception:
			frappe.log_error(message=frappe.get_traceback(), title="Error in on_update_after_submit")

	def send_commission_update_email(self, row, new_commission):
		frappe.log_error(f"Sending Mail, {row.dealer_id}, {new_commission}", "Sending Mail Debug")
		contract = self
		contract_link = f"https://lg.extension/app/crm-contract/{contract.name}"

		try:
			dealer_doc = frappe.get_doc("Dealer", row.dealer_id)
			dealer_email = dealer_doc.email_id

			message = f"""
			<p>Dear {dealer_doc.dealer_name or 'Dealer'},</p>

			<p>We would like to inform you that the commission rate associated with your contract has been updated.</p>

			<p>
				<strong>Contract:</strong> <a href="{contract_link}">{contract.name}</a><br>
				<strong>Dealer ID:</strong> {row.dealer_id}<br>
				<strong>Email:</strong> {dealer_email}<br>
				<strong>Updated Commission Rate:</strong> {new_commission}%
			</p>

			<p>Please review the updated details and confirm your acceptance:</p>

			<p>
				<a href="https://lg.extension/app/crm-contract/{contract.name}" 
					style="padding:10px 20px; background-color:#28a745; color:white; text-decoration:none; border-radius:5px; margin-right:10px;">
					✅ Accept
				</a>

				<a href="https://lg.extension/app/crm-contract/{contract.name}" 
					style="padding:10px 20px; background-color:#dc3545; color:white; text-decoration:none; border-radius:5px;">
					❌ Reject
				</a>
			</p>

			<p>If you have any questions or concerns, please feel free to reach out to us.</p>

			<p>Thank you,<br>
			<strong>LG Contracts Team</strong></p>
			"""

			frappe.sendmail(
				recipients=[dealer_email],
				sender="econnect.himsolutek@lgepartner.com",
				subject=f"Commission Rate Update for Contract {contract.name}",
				message=message,
				reference_doctype="CRM Contract",
				reference_name=contract.name
			)

			frappe.log_error(f"Email sent successfully to {dealer_email} with new commission {new_commission}", "Commission Update Debug")

		except Exception:
			frappe.log_error(message=frappe.get_traceback(), title="Error in send_commission_update_email")


	def on_submit(self):
		self.set_hp_in_deal_and_expiry_date()
		self.send_contract_email_on_submit()

	def before_validate(self):
		self.set_status()

	def validate(self):
		# if self.has_value_changed("custom_contract_status"):
		# 	self.log_status_change()
		self.validate_dates()
		self.validate_currency()
		self.set_status()
		# self.set_hp_in_deal_and_expiry_date()


	def set_hp_in_deal_and_expiry_date(self):
		if self.from_deal and self.expiry_date:
			expiry_date = getdate(self.expiry_date)  # Convert string to date
			deal_doc = frappe.get_doc("CRM Deal", self.from_deal)
			deal_doc.amc_expiry_date = self.expiry_date
			deal_doc.annual_revenue = self.amount
			deal_doc.duplicate_trigger_date = add_months(expiry_date, -1)
			deal_doc.save()
			frappe.db.commit()



	def send_contract_email_on_submit(doc, method=None):
		try:
			if isinstance(doc, str):
				doc = frappe.get_doc("CRM Contract", doc)

			for dealer in doc.dealer:
				try:
					dealer_doc = frappe.get_doc("Dealer", dealer.dealer_id)
					frappe.log_error("dealaer doc", dealer_doc)
					if dealer_doc.email_id:
						send_contract_email(doc, dealer_doc.email_id,dealer_doc.dealer_name,dealer_doc.name)
					else:
						frappe.log_error(f"No email ID for dealer {dealer.dealer_id}", "Contract Email Error")
				except Exception as e:
					frappe.log_error(frappe.get_traceback(), f"Error processing dealer {dealer.dealer_id}")
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Error in send_contract_email_on_submit")



	def log_status_change(self):
		"""Log contract status changes"""
		if not self.is_new():
			old_status = frappe.get_cached_value(self.doctype, self.name, "custom_contract_status")
			if old_status != self.custom_contract_status:
				frappe.get_doc({
					"doctype": "CRM Status Change Log",
					"reference_doctype": self.doctype,
					"reference_name": self.name,
					"status": self.custom_contract_status,
					"from": old_status or "",
					"to": self.custom_contract_status,
					"changed_by": frappe.session.user,
					"changed_on": frappe.utils.now()
				}).insert(ignore_permissions=True)

	def before_save(self):
		if not self.from_deal:
			return

		deal_doc = frappe.get_doc("CRM Deal", self.from_deal)

		# CASE 1: No previous contract linked
		if not deal_doc.from_contract:
			self.contract_type = deal_doc.deal_type
			return

		# CASE 2: Previous contract exists
		previous_contract = frappe.get_doc("CRM Contract", deal_doc.from_contract)

		if not previous_contract.expiry_date:
			return

		expiry_date = getdate(previous_contract.expiry_date)
		expiry_plus_3 = add_months(expiry_date, 3)
		current_date = getdate(today())

		if current_date > expiry_plus_3:
			self.contract_type = "Lost AMC Conversion"
		else:
			self.contract_type = "AMC Renewable"

	def set_status(self):
		try:
			if not self.custom_contract_status:
				today = now_datetime().date()
				if self.expiry_date:
					expiry = getdate(self.expiry_date)
					if expiry < today:
						self.custom_contract_status = "Expired"
					else:
						self.custom_contract_status = "Active"
				else:
					self.custom_contract_status = "Active"
		except Exception as e:
			frappe.log_error(f"Error in set_status for {self.name}", frappe.get_traceback())


	def validate_dates(self):
		if self.start_date and self.expiry_date:
			if getdate(self.start_date) > getdate(self.expiry_date):
				frappe.throw(_("Start Date cannot be after Expiry Date"))

	
	def validate_currency(self):
		# Contracts are created from a quotation: the rate and USD amount are mapped
		# from it, never re-fetched, so the contract keeps the quotation's rate.
		if self.from_quote:
			q = frappe.db.get_value(
				"CRM Quotation", self.from_quote, ["conversion_rate", "total_usd"], as_dict=True
			)
			if q:
				if not flt(self.conversion_rate):
					self.conversion_rate = q.conversion_rate
				if not flt(self.total_usd):
					self.total_usd = q.total_usd
			return

		# Standalone contract (no source quotation): fall back to the Currency Exchange list
		if self.currency and self.price_list_currency and not flt(self.conversion_rate):
			if self.currency == self.price_list_currency:
				self.conversion_rate = 1.0
			else:
				self.conversion_rate = get_exchange_rate(
					self.currency, frappe.db.get_default("currency") or "INR", self.start_date
				)


@frappe.whitelist()
def make_crm_deal(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.date = frappe.utils.nowdate()
		target.valid_till = frappe.utils.add_days(target.date, 30)
		target.status = "Qualification"
		target.deal_type="AMC Renewal"
		target.deal_owner = frappe.session.user
		target.series = "QT.YYYY.-"

	doclist = get_mapped_doc(
		"CRM Contract",
		source_name,
		{
			"CRM Contract": {
				"doctype": "CRM Deal",
				"field_map": {
					"customer": "customer_name",
					"customer_hc": "customer_hc",
					"company": "organization",
					"serial_no": "serial_no",
					"product_name": "product_name",
					"expiry_date": "expiry_date",
					"start_date": "start_date",
				},
				
			},
		},
		target_doc,
		set_missing_values
	)
	return doclist

@frappe.whitelist()
def get_contract_kpis():
	"""Get all contract related KPIs"""
	
	# Get current date for comparisons
	today = frappe.utils.today()
	
	# Total Contracts
	total_contracts = frappe.db.count('CRM Contract')
	
	# Active Contracts (not expired)
	active_contracts = frappe.db.count('CRM Contract', 
		filters={'expiry_date': ['>', today]})
	
	# Expired Contracts
	expired_contracts = frappe.db.count('CRM Contract', 
		filters={'expiry_date': ['<', today]})
	
	# New Conversions (contracts created in last 30 days)
	thirty_days_ago = frappe.utils.add_days(today, -30)
	new_conversions = frappe.db.count('CRM Contract', 
		filters={'creation': ['>=', thirty_days_ago]})
	
	# AMC Renewal (AMC contracts created in last 30 days)
	amc_renewal = frappe.db.count('CRM Contract',
		filters={
			'creation': ['>=', thirty_days_ago],
			'deal_type': 'AMC'
		})
	
	# Lost Conversion (expired contracts in last 30 days)
	lost_conversion = frappe.db.count('CRM Contract',
		filters={
			'expiry_date': ['between', (thirty_days_ago, today)]
		})
	
	# Warranty Conversion (contracts converted from warranty to AMC)
	warranty_conversion = frappe.db.sql("""
		SELECT COUNT(DISTINCT name) 
		FROM `tabCRM Contract`
		WHERE creation >= %s
		AND deal_type = 'AMC'
		AND contract_from = 'CRM Deal'
	""", (thirty_days_ago,))[0][0]
	
	return {
		'total_contracts': total_contracts,
		'active_contracts': active_contracts,
		'expired_contracts': expired_contracts,
		'new_conversions': new_conversions,
		'amc_renewal': amc_renewal,
		'lost_conversion': lost_conversion,
		'warranty_conversion': warranty_conversion
	}

@frappe.whitelist()
def get_pipeline_data(filters=None):
	"""Get pipeline data for dashboard"""
	if isinstance(filters, str):
		filters = json.loads(filters)

	# Default to last 6 months if no date filter
	if not filters or not filters.get('date_range'):
		end_date = frappe.utils.today()
		start_date = frappe.utils.add_months(end_date, -6)
	else:
		date_range = filters['date_range']
		if date_range == 'Last Month':
			start_date = frappe.utils.add_months(frappe.utils.today(), -1)
			end_date = frappe.utils.today()
		elif date_range == 'Last Quarter':
			start_date = frappe.utils.add_months(frappe.utils.today(), -3)
			end_date = frappe.utils.today()
		elif date_range == 'Last Year':
			start_date = frappe.utils.add_months(frappe.utils.today(), -12)
			end_date = frappe.utils.today()
		else:  # Last 6 Months (default)
			start_date = frappe.utils.add_months(frappe.utils.today(), -6)
			end_date = frappe.utils.today()

	# Get contract types distribution
	pipeline_data = frappe.db.sql("""
		SELECT 
			deal_type as name,
			COUNT(*) as count,
			SUM(amount) as value
		FROM `tabCRM Contract`
		WHERE creation BETWEEN %s AND %s
		GROUP BY deal_type
		ORDER BY count DESC
	""", (start_date, end_date), as_dict=1)

	return pipeline_data

@frappe.whitelist()
def get_win_loss_data(filters=None):
	"""Get win/loss ratio data for dashboard"""
	if isinstance(filters, str):
		filters = json.loads(filters)

	# Default to last 6 months if no date filter
	if not filters or not filters.get('date_range'):
		end_date = frappe.utils.today()
		start_date = frappe.utils.add_months(end_date, -6)
	else:
		date_range = filters['date_range']
		if date_range == 'Last Month':
			start_date = frappe.utils.add_months(frappe.utils.today(), -1)
			end_date = frappe.utils.today()
		elif date_range == 'Last Quarter':
			start_date = frappe.utils.add_months(frappe.utils.today(), -3)
			end_date = frappe.utils.today()
		elif date_range == 'Last Year':
			start_date = frappe.utils.add_months(frappe.utils.today(), -12)
			end_date = frappe.utils.today()
		else:  # Last 6 Months (default)
			start_date = frappe.utils.add_months(frappe.utils.today(), -6)
			end_date = frappe.utils.today()

	# Get active vs expired contracts
	status_data = frappe.db.sql("""
		SELECT 
			CASE 
				WHEN expiry_date > CURDATE() THEN 'Active'
				ELSE 'Expired'
			END as status,
			COUNT(*) as count
		FROM `tabCRM Contract`
		WHERE creation BETWEEN %s AND %s
		GROUP BY 
			CASE 
				WHEN expiry_date > CURDATE() THEN 'Active'
				ELSE 'Expired'
			END
	""", (start_date, end_date), as_dict=1)

	return status_data

@frappe.whitelist()
def get_trend_data(filters=None):
	"""Get trend data for dashboard cards"""
	if isinstance(filters, str):
		filters = json.loads(filters)

	# Default to last 6 months if no date filter
	if not filters or not filters.get('date_range'):
		end_date = frappe.utils.today()
		start_date = frappe.utils.add_months(end_date, -6)
	else:
		date_range = filters['date_range']
		if date_range == 'Last Month':
			start_date = frappe.utils.add_months(frappe.utils.today(), -1)
			end_date = frappe.utils.today()
		elif date_range == 'Last Quarter':
			start_date = frappe.utils.add_months(frappe.utils.today(), -3)
			end_date = frappe.utils.today()
		elif date_range == 'Last Year':
			start_date = frappe.utils.add_months(frappe.utils.today(), -12)
			end_date = frappe.utils.today()
		else:  # Last 6 Months (default)
			start_date = frappe.utils.add_months(frappe.utils.today(), -6)
			end_date = frappe.utils.today()

	# Get monthly trends using proper date format
	trend_data = frappe.db.sql("""
		SELECT 
			DATE_FORMAT(creation, '%%Y-%%m') as month,
			COUNT(*) as total_contracts,
			SUM(CASE WHEN deal_type = 'AMC' THEN 1 ELSE 0 END) as amc_contracts,
			SUM(CASE WHEN deal_type = 'Warranty' THEN 1 ELSE 0 END) as warranty_contracts,
			COALESCE(SUM(amount), 0) as total_value
		FROM `tabCRM Contract`
		WHERE creation BETWEEN %s AND %s
		GROUP BY DATE_FORMAT(creation, '%%Y-%%m')
		ORDER BY month
	""", (start_date, end_date), as_dict=1)

	return trend_data


@frappe.whitelist()
def check_advance_payment_reminders():
    today = getdate(nowdate())

    quotations = frappe.get_all(
        "CRM Contract",
        filters={"docstatus": 0},
        fields=["name", "advance_amount", "customer", "owner", "advance_end_date"]
    )

    for q in quotations:
        if not q.advance_amount:
            continue

        doc = frappe.get_doc("CRM Contract", q.name)

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

        if days_due in [1, 20, 25, 30, 60]:
            send_advance_reminder(doc.name, doc.owner, days_due, first_due_row.payment_date)

        # Discontinuation check
        if days_due >= 60:
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
		<p>Regards,<br>Hi-M solutek Pvt. Ltd.</p>
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
	print(f"📌 Triggered discontinuation check for: {doc.name}")
	
	try:
		frappe.log_error(f"Advance not received for Contract: {doc.name}")
		print(f"🔍 Logged error for contract {doc.name}")

		if doc.custom_contract_status != "Discontinue":
			frappe.db.set_value("CRM Contract", doc.name, {
				"custom_contract_status": "Discontinue",
				"discontinue_date": today
			})
			print(f"✅ Status updated to Discontinue for {doc.name} on {today}")
			frappe.db.commit()
			return f"✅ Discontinued: {doc.name}"
		else:
			print(f"ℹ️ Contract {doc.name} already marked as Discontinue")
			return f"⚠️ Already Discontinued: {doc.name}"
	
	except Exception as e:
		print(f"❌ Exception occurred: {str(e)}")
		frappe.log_error(title="Discontinuation Error", message=frappe.get_traceback())
		return f"❌ Failed to update: {doc.name}"



def send_contract_email(doc, email,dealer_name,dealer_id):
	try:

		# Generate PDF file
		try:
			pdf_data = frappe.get_print(
				doc.doctype, doc.name, print_format="AMC Offer", as_pdf=True
			)
			file_name = f"{doc.name}.pdf"
		except Exception:
			frappe.log_error(frappe.get_traceback(), "❌ Failed to generate PDF")
			return "❌ PDF generation failed"

		# Compose email
		message = f"""
		<p>Hi {dealer_name},</p>
		<p>Please find the attached contract for your review.</p>
		<p>Regards,<br>Hi-M Solutek Pvt. Ltd.</p>
		 <p>
			<a href="http://10.101.0.165/api/method/lg.lg.doctype.crm_contract.crm_contract.accept_contract?docname={doc.name}&dealer_id={dealer_id}"style="padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">
			✅ Accept
			</a>
			&nbsp;
			<a href="http://10.101.0.165/api/method/lg.lg.doctype.crm_contract.crm_contract.reject_contract?docname={doc.name}&dealer_id={dealer_id}"style="padding: 10px 20px; background-color: #f44336; color: white; text-decoration: none; border-radius: 5px;">
			❌ Reject
			</a>
		</p>
		"""

		# Send email with PDF attachment
		frappe.sendmail(
			recipients=email,
			sender="econnect.himsolutek@lgepartner.com",
			subject=f"Contract Review - {doc.name}",
			message=message,
			attachments=[{
				"fname": file_name,
				"fcontent": pdf_data,

			}],
			delayed=True,
			queue_separately=True,
			reference_doctype=doc.doctype,
			reference_name=doc.name
		)

		frappe.log_error("✅ Email with PDF sent", f"{email}")
		return "✅ Sent with PDF"

	except Exception:
		frappe.log_error(frappe.get_traceback(), f"❌ Email send failed for {email}")
		return "❌ Failed"

@frappe.whitelist(allow_guest=True)
def accept_contract(docname, dealer_id):
	try:
		doc = frappe.get_doc("CRM Contract", docname)

		dealer_name = None

		# Find matching dealer row
		for d in doc.dealer:
			if d.dealer_id == dealer_id:
				d.status = "Accepted"
				d.sent_time = frappe.utils.now_datetime()
				dealer_name = d.dealer_name
				break
		else:
			frappe.respond_as_web_page(
				"Dealer Not Found",
				f"Dealer {dealer_id} not found in contract {docname}.",
				success=False,
				indicator_color="red",
				primary_action=None,
			)
			return

		# Update contract status
		doc.custom_contract_status = "Accepted"
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		# Notifying the internal team must never break the dealer's confirmation page —
		# the status is already saved and committed above.
		try:
			recipients = []

			dealer_email_r = frappe.db.get_value("Dealer", dealer_id, "email_id")
			if dealer_email_r:
				recipients.append(dealer_email_r)

			# 1️⃣ Region Head (linked via Region field)
			if doc.region:
				region_head = frappe.get_value("Region Master", doc.region, "region_head")
				if region_head:
					recipients.append(region_head)

			# 2️⃣ All users with "Finance" role
			finance_users = frappe.db.sql("""
				SELECT DISTINCT user.name, user.email
				FROM `tabHas Role` hr
				JOIN `tabUser` user ON hr.parent = user.name
				WHERE hr.role = 'Finance' AND user.enabled = 1
			""", as_dict=True)

			for u in finance_users:
				if u.email:
					recipients.append(u.email)

			# Prepare email content
			if recipients:
				contract_id = doc.name
				customer = doc.customer if hasattr(doc, "customer") else "N/A"

				message = f"""
				<p>Dear Team,</p>
				<p>The following contract has been <strong>Accepted</strong> ✅:</p>
				<ul>
					<li><strong>Contract ID:</strong> {contract_id}</li>
					<li><strong>Customer:</strong> {customer}</li>
					<li><strong>Dealer ID:</strong> {dealer_id}</li>
					<li><strong>Dealer Name:</strong> {dealer_name or "N/A"}</li>
					<li><strong>Status:</strong> Accepted</li>
				</ul>
				<p>Thank you,<br>Hi-M Solutek Pvt. Ltd.</p>
				"""

				frappe.sendmail(
					recipients=recipients,
					sender="notify.himsolutek@lgepartner.com",
					subject=f"Contract Accepted - {contract_id}",
					message=message,
					now=True
				)

				# title is capped at 140 chars — keep the recipient list in the message
				frappe.log_error(
					title="Contract Accepted",
					message=f"✅ Notification email sent to: {', '.join(recipients)}"
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Contract Accepted - Notification Failed")

		frappe.respond_as_web_page(
			"Contract Accepted",
			"Contract Accepted successfully",
			success=True,
			indicator_color="green",
			primary_action=None,
		)
		return

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Accept Contract Failed")
		frappe.respond_as_web_page(
			"Something Went Wrong",
			"Failed to accept the contract. Please contact Hi-M Solutek Pvt. Ltd.",
			success=False,
			indicator_color="red",
			primary_action=None,
		)
		return

# @frappe.whitelist(allow_guest=True)
# def accept_contract(docname, dealer_id):
# 	try:
# 		doc = frappe.get_doc("CRM Contract", docname)

# 		# Find matching dealer row
# 		for d in doc.dealer:
# 			if d.dealer_id == dealer_id:
# 				d.status = "Accepted"
# 				d.sent_time = frappe.utils.now_datetime()
# 				break
# 		else:
# 			return f"❌ Dealer {dealer_id} not found in contract"

# 		doc.custom_contract_status = "Accepted"
# 		doc.save(ignore_permissions=True)
# 		frappe.db.commit()
		

# 	except Exception:
# 		frappe.log_error(frappe.get_traceback(), "Accept Contract Failed")
# 		return "❌ Failed to accept"

@frappe.whitelist(allow_guest=True)
def reject_contract(docname, dealer_id):
	try:
		doc = frappe.get_doc("CRM Contract", docname)

		for d in doc.dealer:
			if d.dealer_id == dealer_id:
				d.status = "Rejected"
				d.sent_time = frappe.utils.now_datetime()
				break
		else:
			frappe.respond_as_web_page(
				"Dealer Not Found",
				f"Dealer {dealer_id} not found in contract {docname}.",
				success=False,
				indicator_color="red",
				primary_action=None,
			)
			return

		doc.custom_contract_status = "Rejected"
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		frappe.respond_as_web_page(
			"Contract Rejected",
			"Contract Rejected successfully",
			success=False,
			indicator_color="red",
			primary_action=None,
		)
		return

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Reject Contract Failed")
		frappe.respond_as_web_page(
			"Something Went Wrong",
			"Failed to reject the contract. Please contact Hi-M Solutek Pvt. Ltd.",
			success=False,
			indicator_color="red",
			primary_action=None,
		)
		return




def check_billing_schedule_and_notify():
	print("🔍 Running Billing Schedule Check...")
	contracts = frappe.get_all(
		"CRM Contract",
		filters={"custom_contract_status": ["!=", "Discontinue"]},
		fields=["name", "owner"]
	)

	print(f"Total Active Contracts Found: {len(contracts)}")

	for contract in contracts:
		doc = frappe.get_doc("CRM Contract", contract.name)
		print(f"\n📑 Checking Contract: {doc.name}, Owner: {doc.owner}")

		for row in doc.billing_schedule:
			if not row.billing_date:
				print(f"⏭️ Skipping row (no billing_date) in Contract {doc.name}")
				continue

			# sirf wahi row consider karo jisme is_advance = 0 aur status = Pending ho
			if row.is_advance == 0 and row.status == "Pending":
				days_passed = date_diff(today(), getdate(row.billing_date))
				print(f"➡️ Row Billing Date: {row.billing_date}, Days Passed: {days_passed}, is_discountinue: {row.is_discountinue}")

				# 30-day mail, 60+ discontinue
				if days_passed == 30 and row.is_discountinue == 0:
					print(f"📧 Sending 30-day reminder mail for Contract {doc.name}")
					send_overdue_email(doc, row, days_passed)
					row.db_set("is_discountinue", 1)

				if days_passed >= 60:
					print(f"⚠️ Marking Contract {doc.name} as Discontinue (60+ days)")
					mark_contract_discontinue(doc)


def send_overdue_email(contract_doc, row, days_passed):
	try:
		subject = f"[Reminder] Payment pending for Contract {contract_doc.name}"
		message = f"""
			<p>Hello,</p>
			<p>This is a reminder that payment for <b>Contract {contract_doc.name}</b> 
			with Billing Date <b>{row.billing_date}</b> is still <span style="color:red">pending</span>.</p>
			<p>It has been overdue by <b>{days_passed} days</b>. Please make the payment at the earliest.</p>
			<br>
			<p>Regards,<br>Hi-M Tech Solutek Pvt. Ltd.</p>
		"""
		frappe.sendmail(
			recipients="payal@extensioncrm.com",
			sender="notify.himsolutek@lgepartner.com",
			subject=subject,
			message=message,
			reference_doctype="CRM Contract",
			reference_name=contract_doc.name
		)
		print(f"✅ Email sent to payal@extensioncrm.com for Contract {contract_doc.name}, Billing Date {row.billing_date}")
		frappe.logger().info(
			f"✅ Email sent to payal@extensioncrm.com for Contract {contract_doc.name}, Billing Date {row.billing_date}"
		)
	except Exception:
		print(f"❌ Failed to send email for Contract {contract_doc.name}")
		frappe.log_error(frappe.get_traceback(), "Billing Schedule Email Error")


def mark_contract_discontinue(contract_doc):
	try:
		contract_doc.db_set({
			"custom_contract_status": "Discontinue",
			"discontinue_date": today()   # jis din discontinue ho us din ki date
		})
		print(f"⚠️ Contract {contract_doc.name} marked as Discontinue on {today()}")
		frappe.logger().info(f"⚠️ Contract {contract_doc.name} marked as Discontinue on {today()}")
	except Exception:
		print(f"❌ Error while marking Contract {contract_doc.name} as Discontinue")
		frappe.log_error(frappe.get_traceback(), "Contract Discontinue Error")


def send_monthly_branch_head_reminders():
	"""Monthly job: mail every branch head the pending billing and pending payments of the
	contracts in their branch(es)."""
	for branch_head, reminder in get_branch_head_reminders().items():
		send_branch_head_reminder(branch_head, reminder)


def get_branch_head_reminders(as_on=None):
	"""Return {branch_head: {"billing": [...], "payments": [...]}} where
	billing  = billing rows dated this month whose invoice is not raised yet, and
	payments = invoice payment portions due this month or earlier that are unpaid or
	           partially paid (so they keep coming back every month until fully paid)."""
	month_start = get_first_day(as_on or today())
	values = {"month_start": month_start, "next_month_start": get_first_day(add_months(month_start, 1))}

	pending_billing = frappe.db.sql(
		"""
		SELECT c.name AS contract, c.customer, c.branch, b.billing_term, b.billing_date, b.amount
		FROM `tabContract Billing Schedule` b
		JOIN `tabCRM Contract` c ON c.name = b.parent AND b.parenttype = 'CRM Contract'
		WHERE b.status = 'Pending'
			AND b.billing_date >= %(month_start)s AND b.billing_date < %(next_month_start)s
			AND c.docstatus < 2
			AND IFNULL(c.custom_contract_status, '') NOT IN ('Discontinue', 'Rejected')
		ORDER BY b.billing_date, c.name
		""",
		values,
		as_dict=True,
	)

	pending_payments = frappe.db.sql(
		"""
		SELECT c.name AS contract, c.customer, c.branch, i.invoice AS invoice_no, t.due_date,
			IFNULL(t.portion_amount, 0) AS portion_amount,
			IFNULL(t.amount_received, 0) AS amount_received
		FROM `tabInvoice Payment Term` t
		JOIN `tabInvoice` i ON i.name = t.parent AND t.parenttype = 'Invoice'
		JOIN `tabCRM Contract` c ON c.name = i.amc_contract_id
		WHERE t.due_date < %(next_month_start)s
			AND IFNULL(t.portion_amount, 0) > IFNULL(t.amount_received, 0)
		ORDER BY t.due_date, c.name
		""",
		values,
		as_dict=True,
	)
	for row in pending_payments:
		row.outstanding = flt(row.portion_amount) - flt(row.amount_received)
		if flt(row.amount_received) > 0:
			row.payment_status = "Partially Paid"
		elif getdate(row.due_date) < month_start:
			row.payment_status = "Overdue"
		else:
			row.payment_status = "Due This Month"

	branch_heads = dict(frappe.get_all("Region Branches", fields=["name", "branch_head"], as_list=True))
	reminders = {}
	for key, rows in (("billing", pending_billing), ("payments", pending_payments)):
		for row in rows:
			branch_head = branch_heads.get(row.branch)
			if not branch_head:
				frappe.log_error(
					f"Contract {row.contract}: branch '{row.branch}' has no Branch Head, reminder skipped",
					"Branch Head Reminder",
				)
				continue
			reminders.setdefault(branch_head, {"billing": [], "payments": []})[key].append(row)

	return reminders


def send_branch_head_reminder(branch_head, reminder):
	def table(headers, rows):
		head = "".join(f"<th style='border:1px solid #ccc;padding:4px 8px'>{h}</th>" for h in headers)
		body = "".join(
			"<tr>" + "".join(f"<td style='border:1px solid #ccc;padding:4px 8px'>{cell}</td>" for cell in row) + "</tr>"
			for row in rows
		)
		return f"<table style='border-collapse:collapse'><tr>{head}</tr>{body}</table>"

	sections = []
	if reminder["billing"]:
		sections.append(
			"<p><b>Billing due this month – invoice not raised yet</b></p>"
			+ table(
				["Contract", "Customer", "Branch", "Billing Term", "Billing Date", "Amount"],
				[
					[r.contract, r.customer or "", r.branch, r.billing_term or "", formatdate(r.billing_date), fmt_money(r.amount)]
					for r in reminder["billing"]
				],
			)
		)
	if reminder["payments"]:
		sections.append(
			"<p><b>Payments pending (due this month, overdue or partially paid)</b></p>"
			+ table(
				["Contract", "Customer", "Branch", "Invoice No", "Due Date", "Due Amount", "Received", "Outstanding", "Status"],
				[
					[
						r.contract, r.customer or "", r.branch, r.invoice_no or "", formatdate(r.due_date),
						fmt_money(r.portion_amount), fmt_money(r.amount_received), fmt_money(r.outstanding), r.payment_status,
					]
					for r in reminder["payments"]
				],
			)
		)

	message = f"""
		<p>Hello,</p>
		<p>Please find below the pending billing and payments for the contracts of your branch.</p>
		{"<br>".join(sections)}
		<br>
		<p>Regards,<br>Hi-M Tech Solutek Pvt. Ltd.</p>
	"""
	try:
		frappe.sendmail(
			recipients=[frappe.db.get_value("User", branch_head, "email") or branch_head],
			sender="notify.himsolutek@lgepartner.com",
			subject=f"[Reminder] Pending Billing & Payments – {getdate(today()).strftime('%B %Y')}",
			message=message,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Branch Head Reminder Email Error")




import frappe
import openpyxl
from frappe.utils import nowdate
import datetime

# @frappe.whitelist()
# def process_invoice_excel(file_url):
#     """Process uploaded Excel and update Billing Schedule using Customer PO ID"""
#     try:
#         file_doc = frappe.get_doc("File", {"file_url": file_url})
#         file_path = file_doc.get_full_path()

#         wb = openpyxl.load_workbook(file_path)
#         sheet = wb.active

#         error_log = []

#         for idx, row in enumerate(sheet.iter_rows(values_only=True)):
#             if idx == 0:
#                 continue

#             customer_po_id, amount_received, invoice_id, payment_received_date = row

#             if not customer_po_id:
#                 error_log.append(f"Row {idx+1}: Missing Customer PO ID")
#                 continue

#             # --- Normalize PO ID ---
#             customer_po_id = str(customer_po_id).strip()
#             if customer_po_id.replace('.', '', 1).isdigit():
#                 if '.' in customer_po_id:
#                     customer_po_id = str(int(float(customer_po_id)))
#             # If your PO IDs are fixed length like 001, then:
#             customer_po_id = customer_po_id.zfill(3)

#             # --- Normalize Payment Date ---
#             payment_received_date = parse_excel_date(payment_received_date)

#             contracts = frappe.get_all(
#                 "CRM Contract",
#                 filters={"customer_po_id": customer_po_id},
#                 pluck="name"
#             )

#             if not contracts:
#                 error_log.append(f"Row {idx+1}: No contract found for PO ID {customer_po_id}")
#                 continue

#             for contract_name in contracts:
#                 contract = frappe.get_doc("CRM Contract", contract_name)

#                 # Get unpaid billing rows sorted by payment_date
#                 unpaid_rows = sorted(
#                     [bs for bs in contract.billing_schedule if bs.status != "Paid"],
#                     key=lambda x: x.payment_date or nowdate()
#                 )

#                 if not unpaid_rows:
#                     error_log.append(f"Row {idx+1}: No unpaid rows found for contract {contract_name}")
#                     continue

#                 # Fill only the first unpaid row
#                 first_unpaid = unpaid_rows[0]
#                 first_unpaid.amount_received = amount_received
#                 first_unpaid.invoice_id = invoice_id
#                 first_unpaid.status = "Paid"
#                 first_unpaid.payment_received_date = payment_received_date

#                 contract.save(ignore_permissions=True)

#         frappe.db.commit()

#         if error_log:
#             frappe.log_error("\n".join(error_log), "Invoice Excel Processing Issues")

#         return {"status": "success", "message": "Invoices updated successfully"}

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Invoice Excel Processing Error")
#         frappe.throw("Error while processing invoice Excel. Please check error logs.")


def parse_excel_date(value):
    """Convert Excel date or string (like 14-09-2025) → yyyy-mm-dd"""
    if not value:
        return nowdate()

    if isinstance(value, datetime.datetime):
        return value.date().isoformat()

    if isinstance(value, datetime.date):
        return value.isoformat()

    # Handle string formats like 14-09-2025 or 14/09/2025
    val = str(value).strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(val, fmt).date().isoformat()
        except ValueError:
            continue

    # fallback to today
    return nowdate()


from frappe.utils import add_days, getdate

@frappe.whitelist()
def update_invoice_due_dates(invoice_id, billed_date):
    """Update Invoice Payment Term due_dates based on Payment Term and Contract Billing Schedule billed_date"""

    if not invoice_id or not billed_date:
        frappe.throw("Invoice ID and Billed Date are required")

    invoice = frappe.get_doc("Invoice", invoice_id)

    if not invoice.pay_term:
        frappe.throw(f"No Payment Term found in Invoice {invoice_id}")

    pay_term = frappe.get_doc("Pay Term", invoice.pay_term)

    if not pay_term.payment_term_portions:
        frappe.throw(f"No Payment Term Portions found in Pay Term {pay_term.name}")

    base_date = getdate(billed_date)

    updated_rows = []

    for idx, portion in enumerate(pay_term.payment_term_portions):
        days = portion.days or 0
        due_date = add_days(base_date, days)

        if idx < len(invoice.invoice_payment_term):
            inv_term = invoice.invoice_payment_term[idx]
            frappe.db.set_value(
                "Invoice Payment Term",
                inv_term.name,
                "due_date",
                due_date
            )
            updated_rows.append(inv_term.name)

    frappe.db.commit()
    return {
        "message": f"Updated due dates for {len(updated_rows)} term(s) in Invoice {invoice.name}",
        "updated_terms": updated_rows
    }


def set_status_expired():
    current_date = getdate(today())

    contracts = frappe.get_all(
		"CRM Contract",
		filters=[
			["expiry_date", "is", "set"],
			["expiry_date", "<", current_date],
			["custom_contract_status", "not in", ["Expired", "Discontinue"]],
		],
		fields=["name","custom_contract_status"]
	)

    for opp in contracts:
        frappe.db.set_value(
            "CRM Contract",
            opp.name,
            "custom_contract_status",
            "Expired",
            update_modified=False
        )

    frappe.db.commit()

@frappe.whitelist()
def upload_product_details(file_url, docname):

    import frappe
    import pandas as pd

    file_doc = frappe.get_doc("File", {"file_url": file_url})

    file_path = file_doc.get_full_path()

    df = pd.read_csv(file_path)

    doc = frappe.get_doc("CRM Contract", docname)

    doc.product_details = []

    for _, row in df.iterrows():

        doc.append("product_details", {
            "serial_no": row.get("serial_no"),
            "product_name": row.get("product_name"),
            "product_group": row.get("product_group"),
            "custom_quantity": row.get("custom_quantity"),
            "status": row.get("status"),
            "model_no": row.get("model_no"),
            "category_of_model": row.get("category_of_model"),
            "io": row.get("io"),
            "hp": row.get("hp"),
            "ton": row.get("ton"),
        })

    doc.save(ignore_permissions=True)

    return "success"


import frappe
from frappe.utils import get_url
from frappe.utils.pdf import get_pdf


@frappe.whitelist()
def send_work_order(name):

    doc = frappe.get_doc("CRM Contract", name)

    if doc.docstatus == 2:
        frappe.throw("Cancelled contracts cannot send Work Order.")

    if not doc.branch:
        frappe.throw("Please select a Branch first.")

    # Get Branch Head
    branch_head = frappe.db.get_value(
        "Region Branches",
        doc.branch,
        "branch_head"
    )

    if not branch_head:
        frappe.throw("Branch Head is not set for this Branch.")

    recipients = []

    if branch_head:
        recipients.append(branch_head)

    # Additional emails
    if doc.work_order_additional_emails:
        additional_emails = [
            email.strip()
            for email in doc.work_order_additional_emails.split(",")
            if email.strip()
        ]

        recipients.extend(additional_emails)

    if not recipients:
        frappe.throw("No email recipient found.")

    # Generate PDF from SSD WO print format
    pdf = frappe.get_print(
        "CRM Contract",
        doc.name,
        print_format="SSD WO",
        as_pdf=True
    )

    frappe.sendmail(
        recipients=recipients,
        subject=f"Work Order - {doc.work_order_no or doc.name}",
        message=f"Please find attached the Work Order {doc.name}.",
        attachments=[
            {
                "fname": f"{doc.work_order_no or doc.name}.pdf",
                "fcontent": pdf
            }
        ]
    )
	

    return "Work Order sent successfully."

# ---- Upload Billing (list view button) ----------------------------------------------------
# Excel column -> accepted header spellings (headers are lower-cased, non-alphanumerics -> "_")
BILLING_UPLOAD_COLUMNS = {
	"customer_name": ["customer_name", "customer"],
	"start_date": ["start_date"],
	"bill_ship_code": ["bill_to_code", "bill_ship_code", "bill_to_ship_to_code", "bill_ship_to_code"],
	"expiry_date": ["expiry_date", "end_date"],
	"region": ["region"],
	"branch": ["branch"],
	"amount": ["amount", "contract_amount"],
	"billing_terms": ["billing_terms", "billing_term", "payment_frequency"],
	"billed_date": ["billed_date", "billing_date", "invoice_date"],
	"invoice_id": ["invoice_id", "invoice_no", "invoice_number"],
}
BILLING_UPLOAD_OPTIONAL = {"billing_terms", "billed_date", "invoice_id"}


def _billing_header_key(value):
	return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _billing_cell_date(value):
	if value in (None, ""):
		return None
	if isinstance(value, (datetime.datetime, datetime.date)):
		return getdate(value)
	text = str(value).strip()
	for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%Y/%m/%d"):
		try:
			return datetime.datetime.strptime(text, fmt).date()
		except ValueError:
			pass
	return getdate(text)


def _billing_ordinal(n):
	suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
	return f"{n}{suffix} Term"


def _billing_cell_text(value):
	if value is None:
		return ""
	if isinstance(value, float) and value.is_integer():
		value = int(value)
	return str(value).strip()


@frappe.whitelist()
def upload_billing(file_url):
	"""Update CRM Contract billing_schedule rows from an uploaded Billing Template (.xlsx).

	Each Excel row is matched to exactly one contract on customer name, start date, bill/ship
	code, expiry date, region, branch and amount. Each Excel row (the 1st, 2nd, ... for a
	contract) fills the first billing_schedule row whose Invoice Number and Billed Date are both
	blank; already billed rows are passed over. If no such row is left, that Excel row is skipped
	with a reason naming the contract. Each filled row gets billed_date, invoice_id and status
	"Invoice Raised"; the contract's payment_frequency is set from the billing terms column.
	"""
	import openpyxl

	frappe.has_permission("CRM Contract", "write", throw=True)
	path = frappe.get_doc("File", {"file_url": file_url}).get_full_path()
	ws = openpyxl.load_workbook(path, data_only=True, read_only=True).active

	rows = ws.iter_rows(values_only=True)
	headers = [_billing_header_key(h) for h in next(rows, [])]
	index, missing = {}, []
	for field, aliases in BILLING_UPLOAD_COLUMNS.items():
		pos = next((headers.index(a) for a in aliases if a in headers), None)
		if pos is None:
			if field not in BILLING_UPLOAD_OPTIONAL or field == "billing_terms":
				missing.append(field)
		else:
			index[field] = pos
	if missing:
		frappe.throw(_("Missing column(s) in Excel: {0}").format(", ".join(missing)))

	frequencies = {
		re.sub(r"[^a-z]", "", f.lower()): f
		for f in frappe.get_meta("CRM Contract").get_field("payment_frequency").options.split("\n") if f
	}
	frequencies.update({"quaterly": "Quarterly", "yearly": "Annually", "annual": "Annually",
		"halfyearly": "Semi-Annually", "semiannually": "Semi-Annually"})

	key_fields = ["customer_name", "start_date", "bill_ship_code", "expiry_date", "region", "branch", "amount"]
	docs, errors, filled, used, current = {}, [], {}, {}, None
	for line, row in enumerate(rows, start=2):
		cell = lambda f: row[index[f]] if f in index else None
		# a row with only a billed date / invoice (+ terms) is the next term of the previous contract
		is_key_row = any(_billing_cell_text(cell(f)) for f in key_fields)
		if not is_key_row and not (_billing_cell_text(cell("billed_date")) or _billing_cell_text(cell("invoice_id"))):
			continue
		try:
			if is_key_row:
				current = None
				filters = {
					"customer_name": _billing_cell_text(cell("customer_name")),
					"start_date": _billing_cell_date(cell("start_date")),
					"bill_ship_code": _billing_cell_text(cell("bill_ship_code")),
					"expiry_date": _billing_cell_date(cell("expiry_date")),
					"region": _billing_cell_text(cell("region")),
					"branch": _billing_cell_text(cell("branch")),
					"amount": flt(cell("amount")),
				}
				matches = frappe.get_all("CRM Contract", filters=filters, pluck="name")
				if not matches:
					errors.append(_("Row {0}: no matching contract").format(line))
					continue
				if len(matches) > 1:
					errors.append(_("Row {0}: {1} contracts match ({2})").format(line, len(matches), ", ".join(matches)))
					continue

				if matches[0] not in docs:
					doc = frappe.get_doc("CRM Contract", matches[0])
					terms = re.sub(r"[^a-z]", "", _billing_cell_text(cell("billing_terms")).lower())
					if terms:
						frequency = frequencies.get(terms)
						if not frequency:
							errors.append(_("Row {0}: unknown billing terms '{1}'").format(line, cell("billing_terms")))
							continue
						doc.payment_frequency = frequency
					docs[doc.name] = doc
					filled[doc.name] = 0
					used[doc.name] = set()
				current = matches[0]
			elif not current:
				errors.append(_("Row {0}: previous contract was not matched, row skipped").format(line))
				continue

			doc = docs[current]
			billed = _billing_cell_date(cell("billed_date"))
			# first schedule row not yet billed (Invoice Number and Billed Date blank) and not
			# already filled by an earlier Excel row; rows already billed are skipped
			sched = next(
				(s for s in doc.billing_schedule
					if not s.invoice_id and not s.billed_date and s.name not in used[current]),
				None,
			)
			if not sched:
				errors.append(_(
					"Row {0}: contract {1} skipped - no billing schedule row with blank Invoice Number and Billed Date"
				).format(line, doc.name))
				continue
			used[current].add(sched.name)
			sched.billed_date = billed
			if not sched.billing_date:
				sched.billing_date = billed
			sched.invoice_id = _billing_cell_text(cell("invoice_id"))
			sched.status = "Invoice Raised"
			filled[current] += 1
		except Exception as e:
			errors.append(_("Row {0}: {1}").format(line, str(e)))

	updated = []
	for doc in docs.values():
		if not filled[doc.name]:
			continue
		doc.flags.ignore_validate_update_after_submit = True
		doc.flags.ignore_mandatory = True
		try:
			doc.save()
			updated.append(doc.name)
		except Exception as e:
			errors.append(_("{0}: could not save - {1}").format(doc.name, str(e)))
	return {"updated": sorted(updated), "errors": errors}


# ---- Upload Payment (list view button) ----------------------------------------------------
PAYMENT_UPLOAD_COLUMNS = {
	"customer_name": ["customer_name", "customer"],
	"invoice_id": ["invoice_no", "invoice_id", "invoice_number"],
	"amount": ["amount", "amount_loc"],
	"overdue_amount": ["overdue_amount", "overdue_amount_loc", "overdue"],
}


def _billing_number_text(value):
	return str(int(value)) if float(value).is_integer() else str(value)


@frappe.whitelist()
def upload_payment(file_url):
	"""Update CRM Contract billing_schedule rows from an uploaded Payment sheet (.xlsx).

	Only the Customer Name, Invoice No., Amount and Overdue Amount columns are read; every other
	column is ignored. The contract is found on customer name and the billing_schedule row on
	invoice_id = Invoice No. For a matched row:
	- Overdue Amount is 0: received_amount = Excel Amount, overdue_amount = Excel Amount - received.
	- Overdue Amount is not 0: overdue_amount = Excel Overdue Amount, received_amount = Excel Amount - overdue.
	payment_date is set to today and status becomes "Paid" (nothing overdue) or "Partially Paid".
	Rows that cannot be matched are reported with a reason.
	"""
	import openpyxl

	frappe.has_permission("CRM Contract", "write", throw=True)
	path = frappe.get_doc("File", {"file_url": file_url}).get_full_path()
	ws = openpyxl.load_workbook(path, data_only=True, read_only=True).active

	rows = ws.iter_rows(values_only=True)
	headers = [_billing_header_key(h) for h in next(rows, [])]
	index, missing = {}, []
	for field, aliases in PAYMENT_UPLOAD_COLUMNS.items():
		pos = next((headers.index(a) for a in aliases if a in headers), None)
		if pos is None:
			missing.append(field)
		else:
			index[field] = pos
	if missing:
		frappe.throw(_("Missing column(s) in Excel: {0}").format(", ".join(missing)))

	docs, errors, contracts_by_customer = {}, [], {}
	for line, row in enumerate(rows, start=2):
		cell = lambda f: row[index[f]] if index[f] < len(row) else None
		customer_name = _billing_cell_text(cell("customer_name"))
		invoice_id = _billing_cell_text(cell("invoice_id"))
		if not (customer_name or invoice_id):
			continue
		try:
			if not customer_name or not invoice_id:
				errors.append(_("Row {0}: customer name and invoice number are required").format(line))
				continue

			key = customer_name.lower()
			if key not in contracts_by_customer:
				contracts_by_customer[key] = frappe.get_all(
					"CRM Contract", filters={"customer_name": customer_name, "docstatus": ["<", 2]}, pluck="name")
			contracts = contracts_by_customer[key]
			if not contracts:
				errors.append(_("Row {0}: no contract found for customer {1}").format(line, customer_name))
				continue

			matches = []
			for name in contracts:
				if name not in docs:
					docs[name] = frappe.get_doc("CRM Contract", name)
				sched = next((s for s in docs[name].billing_schedule if _billing_cell_text(s.invoice_id) == invoice_id), None)
				if sched:
					matches.append((docs[name], sched))
			if not matches:
				errors.append(_("Row {0}: no billing schedule row with invoice number {1} for customer {2}").format(
					line, invoice_id, customer_name))
				continue
			if len(matches) > 1:
				errors.append(_("Row {0}: invoice number {1} found in {2} contracts ({3})").format(
					line, invoice_id, len(matches), ", ".join(d.name for d, _s in matches)))
				continue

			doc, sched = matches[0]
			excel_amount = flt(cell("amount"), 2)
			excel_overdue = flt(cell("overdue_amount"), 2)
			if excel_overdue:
				overdue = excel_overdue
				received = flt(excel_amount - excel_overdue, 2)
			else:
				received = excel_amount
				overdue = flt(excel_amount - received, 2)
			if received < 0 or overdue < 0:
				errors.append(_("Row {0}: contract {1}: invoice {2} gives a negative received/overdue amount "
					"(Amount {3}, Overdue Amount {4}); row not updated").format(
					line, doc.name, invoice_id, excel_amount, excel_overdue))
				continue

			sched.received_amount = _billing_number_text(received)
			sched.overdue_amount = overdue
			sched.payment_date = str(getdate(nowdate()))
			sched.status = "Partially Paid" if overdue else "Paid"
			doc.flags.payment_updated = True
		except Exception as e:
			errors.append(_("Row {0}: {1}").format(line, str(e)))

	updated = []
	for doc in docs.values():
		if not doc.flags.payment_updated:
			continue
		doc.flags.ignore_validate_update_after_submit = True
		doc.flags.ignore_mandatory = True
		try:
			doc.save()
			updated.append(doc.name)
		except Exception as e:
			errors.append(_("{0}: could not save - {1}").format(doc.name, str(e)))
	return {"updated": sorted(updated), "errors": errors}


# ---- Upload AMC Billing (list view button) ------------------------------------------------
# Customer's "AMC Raw data" sheet (.xlsb / .xlsx). One Excel row = one invoice = one billing term.
AMC_BILLING_COLUMNS = {
	"bill_to_code": ["customer_bill_to_code", "bill_to_code"],
	"customer_name": ["customer_name"],
	"invoice_no": ["invoice_no", "invoice_number"],
	"invoice_date": ["invoice_date"],
	"wty_start": ["wty_start_date"],
	"wty_end": ["wty_end_date"],
	"total": ["total", "amount"],
	"ext_type": ["wty_ext_type"],
	"branch": ["actual_branch", "branch"],
}
AMC_BILLING_OPTIONAL = {"bill_to_code", "ext_type", "wty_end", "branch"}


def _amc_cell_date(value):
	# .xlsb (and un-formatted .xlsx) dates arrive as Excel serial numbers
	if isinstance(value, (int, float)) and not isinstance(value, bool):
		return getdate(datetime.date(1899, 12, 30) + datetime.timedelta(days=int(value)))
	return _billing_cell_date(value)


def _amc_read_rows(path):
	"""Yield the header-keyed rows of the first usable sheet ('Working' when present)."""
	if path.lower().endswith(".xlsb"):
		try:
			from pyxlsb import open_workbook
		except ImportError:
			frappe.throw(_("Reading .xlsb needs the pyxlsb package (bench pip install pyxlsb), or upload the sheet as .xlsx"))
		with open_workbook(path) as wb:
			sheet = "Working" if "Working" in wb.sheets else wb.sheets[0]
			with wb.get_sheet(sheet) as ws:
				return [[c.v for c in row] for row in ws.rows()]
	import openpyxl

	wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
	ws = wb["Working"] if "Working" in wb.sheetnames else wb.active
	return [list(row) for row in ws.iter_rows(values_only=True)]


def _amc_frequency(ext_type):
	"""Billing frequency from the 'WTY EXT Type' text: 'Quarterly  AMC' -> Quarterly, 'Half Yearly AMC' /
	'Labor - Half Yearly AMC' -> Semi-Annually, any '1 Year' / '1Yr' plan -> Annually, else None."""
	text = (ext_type or "").lower()
	if "month" in text:
		return "Monthly"
	if "quarter" in text or "quater" in text:
		return "Quarterly"
	if "half" in text or "semi" in text:
		return "Semi-Annually"
	# '... 1 Year ...', 'Platinum Plan - 1Yr Normal AMC', 'Labor - 1yr AMC', 'Yearly', 'Annual'
	if re.search(r"\d\s*-?\s*(yr|year)|\byear|\bannual|\byr", text):
		return "Annually"
	return None  # unreadable ('0x2a', 0, blank): try every frequency


def _amc_billing_dates(start_date, expiry_date, frequency, billing_terms):
	"""Billing dates of a contract, same rule as generate_billing_schedule() in crm_contract.js:
	Advance bills at the start of every period, Post at the end of every period."""
	months = {"Monthly": 1, "Quarterly": 3, "Semi-Annually": 6, "Annually": 12}.get(frequency)
	if not months:
		return []
	start, end = getdate(start_date), getdate(expiry_date)
	dates = [start] if billing_terms == "Advance" else []
	current = start
	while True:
		nxt = add_months(current, months)
		if nxt > end:
			dates.append(end)
			break
		dates.append(nxt)
		current = nxt
	if billing_terms == "Advance" and len(dates) > 1:
		dates.pop()
	return dates


def _amc_regenerate_schedule(doc, dates):
	min_days = 0
	if doc.payment_term and frappe.db.exists("Pay Term", doc.payment_term):
		portions = frappe.get_doc("Pay Term", doc.payment_term).payment_term_portions
		min_days = min([p.days or 0 for p in portions] or [0])
	each = flt(flt(doc.amount) / len(dates), 2)
	doc.set("billing_schedule", [])
	for i, d in enumerate(dates):
		doc.append("billing_schedule", {
			"billing_date": d,
			"payment_date": str(add_days(d, min_days)),
			"amount": each if i < len(dates) - 1 else flt(flt(doc.amount) - each * (len(dates) - 1), 2),
			"billing_term": _billing_ordinal(i + 1),
			"status": "Pending",
		})


@frappe.whitelist()
def upload_amc_billing(file_url, dry_run=0):
	"""Fill the billing terms of saved CRM Contracts from the customer's AMC Raw data sheet.

	A blank Invoice Date on a row that has an Invoice No takes the Invoice Date of the row above.
	Every Excel row (customer bill-to code / name, WTY Start Date, WTY End Date, Invoice No,
	Invoice Date, Total, WTY EXT Type) is one billing term of one contract:
	- The contract is found on Bill To Code (Customer Name when either side has no code), Actual
	  Branch = its Branch, Zone = its Region (or EAST for EAST-1 / EAST-2), and the WTY Start Date
	  has to fall inside its Start / Expiry Date. No contract is ever created.
	- WTY Start Date is the billing date of the billing term. It is checked against the contract's
	  billing schedule dates under Advance and under Post (frequency = the contract's Billing
	  Terms, else read from WTY EXT Type); the one that has a billing date on it becomes the
	  contract's Payment Frequency (billing_terms). When both fit (every date but the first/last
	  one does) Advance is taken.
	- Total x the number of terms of that frequency (Semi-Annually: Total x 2) must equal the
	  contract Amount (0.5% rounding allowed); this picks the right contract when a customer has
	  several at the same branch. The contract Amount itself is never changed.
	- The billing schedule is (re)generated for that frequency unless billing already started on
	  it; the term is then filled with Amount = Total, Invoice Number, Billed Date and status
	  "Invoice Raised" (a Paid / Partially Paid term keeps its status). A term missing from an
	  already billed schedule is added.
	With dry_run nothing is saved; the same report is returned.
	"""
	frappe.has_permission("CRM Contract", "write", throw=True)
	dry_run = int(dry_run or 0)
	path = frappe.get_doc("File", {"file_url": file_url}).get_full_path()
	rows = _amc_read_rows(path)
	headers = [_billing_header_key(h) for h in (rows[0] if rows else [])]
	index, missing = {}, []
	for field, aliases in AMC_BILLING_COLUMNS.items():
		pos = next((headers.index(a) for a in aliases if a in headers), None)
		if pos is None:
			if field not in AMC_BILLING_OPTIONAL:
				missing.append(field)
		else:
			index[field] = pos
	if missing:
		frappe.throw(_("Missing column(s) in Excel: {0}").format(", ".join(missing)))

	contracts = frappe.get_all(
		"CRM Contract",
		filters={"docstatus": ["<", 2]},
		fields=["name", "customer_name", "bill_ship_code", "start_date", "expiry_date", "payment_frequency", "billing_terms", "amount", "branch"],
	)
	norm = lambda v: re.sub(r"\s+", " ", _billing_cell_text(v)).lower()
	by_code, by_name = {}, {}
	for c in contracts:
		if not (c.start_date and c.expiry_date):
			continue
		by_name.setdefault(norm(c.customer_name), []).append(c)
		if c.bill_ship_code:
			by_code.setdefault(norm(c.bill_ship_code), []).append(c)

	last_invoice_date = None  # a blank Invoice Date takes the one of the row above
	errors, failed, seen, assigned = [], [], set(), {}  # assigned: contract -> [(line, term_row, {terms that fit})]
	for line, row in enumerate(rows[1:], start=2):
		cell = lambda f: row[index[f]] if f in index and index[f] < len(row) else None
		invoice_no = _billing_cell_text(cell("invoice_no"))
		customer = _billing_cell_text(cell("customer_name"))
		if not (invoice_no or customer):
			continue
		try:
			total = flt(cell("total"), 2)
			wty_start, invoice_date = _amc_cell_date(cell("wty_start")), _amc_cell_date(cell("invoice_date"))
			if invoice_date:
				last_invoice_date = invoice_date
			elif invoice_no:
				# only a row that has an Invoice No is a billed term; one without stays "not billed yet"
				invoice_date = last_invoice_date
			if not (invoice_no and invoice_date):
				errors.append(_("Row {0}: {1} not billed yet (no Invoice No / Invoice Date), skipped").format(line, customer))
				continue
			if not wty_start:
				errors.append(_("Row {0}: invoice {1} has no WTY Start Date, skipped").format(line, invoice_no))
				continue
			if total <= 0:
				errors.append(_("Row {0}: invoice {1} has no positive Total, skipped").format(line, invoice_no))
				continue
			key = (norm(customer), invoice_no, wty_start)
			if key in seen:
				errors.append(_("Row {0}: invoice {1} repeated for the same term, skipped").format(line, invoice_no))
				continue
			seen.add(key)

			code = norm(cell("bill_to_code"))
			pool = by_code.get(code) or [] if code else []
			named = by_name.get(norm(customer), [])
			# a contract without a bill-to code can only be matched on the customer name
			candidates = {c.name: c for c in pool + [c for c in named if not c.bill_ship_code or not code]}.values()
			candidates = [c for c in candidates if getdate(c.start_date) <= wty_start <= getdate(c.expiry_date)]
			# one customer has contracts at several locations: the sheet's Actual Branch is the
			# contract's Branch (Zone is not compared, the system splits e.g. EAST into EAST-1 / EAST-2)
			branch = norm(cell("branch"))
			in_location = [c for c in candidates if not branch or norm(c.branch) == branch]
			if candidates and not in_location:
				errors.append(_("Row {0}: {1} has contract(s) {2} but not in branch {3}").format(
					line, customer, ", ".join(c.name for c in candidates), _billing_cell_text(cell("branch"))))
				continue
			candidates = in_location
			if not candidates:
				errors.append(_("Row {0}: no saved contract for {1} ({2}) covering WTY Start {3}").format(
					line, customer, _billing_cell_text(cell("bill_to_code")) or "no bill-to code", wty_start))
				continue

			frequency_hint = _amc_frequency(_billing_cell_text(cell("ext_type")))
			hits, amount_mismatch = [], []
			for c in candidates:
				# the contract's own frequency first, then the one the sheet's plan name says, then the
				# rest: Total x terms = Amount is what tells the real frequency (a contract saved
				# as Quarterly can be billed monthly)
				frequencies = [f for f in dict.fromkeys(
					[c.payment_frequency, frequency_hint, "Quarterly", "Semi-Annually", "Annually", "Monthly"]) if f]
				fits = {(f, t) for f in frequencies
					for t in ([c.billing_terms] if c.billing_terms else ["Advance", "Post"])
					if wty_start in _amc_billing_dates(c.start_date, c.expiry_date, f, t)}
				# the invoice is one term: Total x number of terms = the contract Amount
				# (Semi-Annually, 2 terms: Total x 2), allowing for rounding
				amount_fits = {(f, t) for f, t in fits
					if abs(total * len(_amc_billing_dates(c.start_date, c.expiry_date, f, t)) - flt(c.amount)) <= max(1, flt(c.amount) * 0.005)}
				if amount_fits:
					hits.append((c, amount_fits, frequencies))
				elif fits:
					amount_mismatch.append("{0} ({1})".format(c.name, flt(c.amount)))
			if not hits and amount_mismatch:
				errors.append(_("Row {0}: invoice {1} Total {2} x number of terms does not match the Amount of {3}").format(
					line, invoice_no, total, ", ".join(amount_mismatch)))
				continue
			if not hits:
				errors.append(_("Row {0}: WTY Start {1} is not a billing date (Advance or Post) of {2}").format(
					line, wty_start, ", ".join(c.name for c in candidates)))
				continue
			if len(hits) > 1:
				errors.append(_("Row {0}: WTY Start {1} fits {2} contracts ({3}), skipped").format(
					line, wty_start, len(hits), ", ".join(h[0].name for h in hits)))
				continue
			contract, fits, frequencies = hits[0]
			assigned.setdefault(contract.name, []).append((line, {
				"wty_start": wty_start, "invoice_no": invoice_no, "invoice_date": invoice_date,
				"total": total, "frequencies": frequencies,
			}, fits))
		except Exception as e:
			errors.append(_("Row {0}: {1}").format(line, str(e)))
			failed.append(errors[-1])

	updated = []
	for name, items in assigned.items():
		try:
			doc = frappe.get_doc("CRM Contract", name)
			# a Payment Term that no longer exists makes the save fail ("Could not find Payment Term")
			if doc.payment_term and not frappe.db.exists("Pay Term", doc.payment_term):
				doc.payment_term = None
			rows_text = ", ".join(str(item[0]) for item in items)
			# every term of the contract has to agree on one frequency and on Advance / Post
			terms_fit = set.intersection(*(item[2] for item in items))
			if not terms_fit:
				errors.append(_("Rows {1}: contract {0} skipped, its WTY Start Dates do not fit one frequency with Advance / Post").format(
					name, rows_text))
				continue
			order = items[0][1]["frequencies"]
			frequency, billing_terms = min(terms_fit, key=lambda ft: (ft[1] != "Advance", order.index(ft[0]) if ft[0] in order else 9))

			started = any(s.invoice_id or s.billed_date or (s.status and s.status != "Pending") for s in doc.billing_schedule)
			if not started and (not doc.billing_schedule or doc.billing_terms != billing_terms or doc.payment_frequency != frequency):
				doc.billing_terms, doc.payment_frequency = billing_terms, frequency
				_amc_regenerate_schedule(doc, _amc_billing_dates(doc.start_date, doc.expiry_date, frequency, billing_terms))
			else:
				doc.billing_terms, doc.payment_frequency = doc.billing_terms or billing_terms, frequency

			filled = 0
			for line, term, _fits in items:
				sched = next((s for s in doc.billing_schedule if s.billing_date and getdate(s.billing_date) == term["wty_start"]), None)
				if not sched:
					sched = doc.append("billing_schedule", {
						"billing_date": term["wty_start"],
						"billing_term": _billing_ordinal(len(doc.billing_schedule) + 1),
						"status": "Pending",
					})
				if sched.invoice_id and _billing_cell_text(sched.invoice_id) != term["invoice_no"]:
					errors.append(_("Row {0}: contract {1} term {2} already has invoice {3}, skipped").format(
						line, name, term["wty_start"], sched.invoice_id))
					continue
				sched.amount = term["total"]
				sched.invoice_id = term["invoice_no"]
				sched.billed_date = term["invoice_date"]
				if not sched.status or sched.status == "Pending":
					sched.status = "Invoice Raised"
				filled += 1
			if not filled:
				continue
			doc.billing_schedule.sort(key=lambda s: getdate(s.billing_date) if s.billing_date else datetime.date.max)
			for i, s in enumerate(doc.billing_schedule, start=1):
				s.idx = i
			if not dry_run:
				doc.flags.ignore_validate_update_after_submit = True
				doc.flags.ignore_mandatory = True
				try:
					doc.save()
				except Exception as e:
					errors.append(_("Rows {2}: contract {0} could not save - {1}").format(name, str(e), rows_text))
					failed.append(errors[-1])
					continue
			updated.append("{0} ({1}, {2}, {3} term(s))".format(name, billing_terms, frequency, filled))
		except Exception as e:
			errors.append(_("Rows {2}: contract {0}: {1}").format(name, str(e), ", ".join(str(i[0]) for i in items)))
			failed.append(errors[-1])

	if not dry_run:
		_amc_log_upload(file_url, updated, [e for e in errors if e not in failed], failed)
	return {"updated": sorted(updated), "errors": errors, "dry_run": dry_run}


def _amc_log_upload(file_url, updated, skipped, failed):
	"""Write the outcome of an Upload AMC Billing run to the Error Log list, one entry each for the
	updated, the skipped and the failed rows, so they can be looked up (search "Upload AMC Billing")."""
	run = "{0} by {1}".format(frappe.utils.now(), frappe.session.user)
	for label, lines in (("Updated", updated), ("Skipped", skipped), ("Failed", failed)):
		if lines:
			frappe.log_error(
				title="Upload AMC Billing - {0} ({1})".format(label, len(lines)),
				message="File: {0}\nRun: {1}\n{2}: {3}\n\n{4}".format(
					file_url, run, label, len(lines), "\n".join(lines)),
			)
