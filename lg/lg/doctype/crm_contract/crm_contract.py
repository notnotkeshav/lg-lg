# Copyright (c) 2024, extension and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, add_months, date_diff,today,add_days
import json
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.model.mapper import get_mapped_doc
from frappe.utils import now_datetime,getdate,nowdate

from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import add_status_change_log
from dateutil.relativedelta import relativedelta


class CRMContract(Document):
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
		deal.register_date = now_datetime().date()
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
		self.set_contract_in_customer()
	
	def set_contract_in_customer(self):
		if not self.customer:
			frappe.throw("Please select a Customer before submitting the Contract")

		customer = frappe.get_doc("CRM Organization", self.customer)
		print(customer,"customer")
		# Add new row in child table
		customer.append("contracts_information", {
			"contract_id": self.name,
			"start_date": self.start_date,
			"expiry_date": self.expiry_date,
			"status": self.custom_contract_status
		})

		# Save customer record
		customer.save(ignore_permissions=True)
		frappe.db.commit()

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
			deal_doc.hp_under_amc = self.total_hp
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
		if self.currency and self.price_list_currency:
			if self.currency == self.price_list_currency:
				self.conversion_rate = 1.0
				self.price_list_exchange_rate = 1.0
			else:
				# Get exchange rates
				self.conversion_rate = get_exchange_rate(self.currency, self.company_currency)
				self.price_list_exchange_rate = get_exchange_rate(self.price_list_currency, self.currency)


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
        fields=["name", "advance_amount", "customer", "owner", "advance_end_date", "is_govt"]
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

        # Govt or non-govt reminder logic
        if (q.is_govt == 0 and days_due in [1, 20, 25, 30]) or \
           (q.is_govt == 1 and days_due in [1, 20, 25, 30, 60]):

            send_advance_reminder(doc.name, doc.owner, days_due, first_due_row.payment_date)

        # Discontinuation check
        if (q.is_govt == 0 and days_due >= 30) or \
           (q.is_govt == 1 and days_due >= 60):

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
		fields=["name", "owner", "is_govt"]
	)

	print(f"Total Active Contracts Found: {len(contracts)}")

	for contract in contracts:
		doc = frappe.get_doc("CRM Contract", contract.name)
		print(f"\n📑 Checking Contract: {doc.name}, Owner: {doc.owner}, Govt: {doc.is_govt}")

		for row in doc.billing_schedule:
			if not row.billing_date:
				print(f"⏭️ Skipping row (no billing_date) in Contract {doc.name}")
				continue

			# sirf wahi row consider karo jisme is_advance = 0 aur status = Pending ho
			if row.is_advance == 0 and row.status == "Pending":
				days_passed = date_diff(today(), getdate(row.billing_date))
				print(f"➡️ Row Billing Date: {row.billing_date}, Days Passed: {days_passed}, is_discountinue: {row.is_discountinue}")

				# Govt vs Non-Govt logic
				if doc.is_govt == 0:
					# Non-Govt: 30-day mail, 60+ discontinue
					if days_passed == 30 and row.is_discountinue == 0:
						print(f"📧 Sending 30-day reminder mail for Contract {doc.name}")
						send_overdue_email(doc, row, days_passed)
						row.db_set("is_discountinue", 1)

					if days_passed >= 60:
						print(f"⚠️ Marking Contract {doc.name} as Discontinue (Non-Govt, 60+ days)")
						mark_contract_discontinue(doc)

				elif doc.is_govt == 1:
					# Govt: 60-day mail, 60+ discontinue
					if days_passed == 60 and row.is_discountinue == 0:
						print(f"📧 Sending 60-day reminder mail for Contract {doc.name}")
						send_overdue_email(doc, row, days_passed)
						frappe.db.set_value(
							"Contract Billing Schedule",
							row.name,
							"is_discountinue",
							1
						)


					if days_passed > 60:
						print(f"⚠️ Marking Contract {doc.name} as Discontinue (Govt, >60 days)")
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




import frappe
import openpyxl
from frappe.utils import nowdate
import datetime

@frappe.whitelist()
def process_invoice_excel(file_url):
    """Process uploaded Excel and update Billing Schedule using Customer PO ID"""
    try:
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        file_path = file_doc.get_full_path()

        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active

        error_log = []

        for idx, row in enumerate(sheet.iter_rows(values_only=True)):
            if idx == 0:
                continue

            customer_po_id, amount_received, invoice_id, payment_received_date = row

            if not customer_po_id:
                error_log.append(f"Row {idx+1}: Missing Customer PO ID")
                continue

            # --- Normalize PO ID ---
            customer_po_id = str(customer_po_id).strip()
            if customer_po_id.replace('.', '', 1).isdigit():
                if '.' in customer_po_id:
                    customer_po_id = str(int(float(customer_po_id)))
            # If your PO IDs are fixed length like 001, then:
            customer_po_id = customer_po_id.zfill(3)

            # --- Normalize Payment Date ---
            payment_received_date = parse_excel_date(payment_received_date)

            contracts = frappe.get_all(
                "CRM Contract",
                filters={"customer_po_id": customer_po_id},
                pluck="name"
            )

            if not contracts:
                error_log.append(f"Row {idx+1}: No contract found for PO ID {customer_po_id}")
                continue

            for contract_name in contracts:
                contract = frappe.get_doc("CRM Contract", contract_name)

                # Get unpaid billing rows sorted by payment_date
                unpaid_rows = sorted(
                    [bs for bs in contract.billing_schedule if bs.status != "Paid"],
                    key=lambda x: x.payment_date or nowdate()
                )

                if not unpaid_rows:
                    error_log.append(f"Row {idx+1}: No unpaid rows found for contract {contract_name}")
                    continue

                # Fill only the first unpaid row
                first_unpaid = unpaid_rows[0]
                first_unpaid.amount_received = amount_received
                first_unpaid.invoice_id = invoice_id
                first_unpaid.status = "Paid"
                first_unpaid.payment_received_date = payment_received_date

                contract.save(ignore_permissions=True)

        frappe.db.commit()

        if error_log:
            frappe.log_error("\n".join(error_log), "Invoice Excel Processing Issues")

        return {"status": "success", "message": "Invoices updated successfully"}

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Invoice Excel Processing Error")
        frappe.throw("Error while processing invoice Excel. Please check error logs.")


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
