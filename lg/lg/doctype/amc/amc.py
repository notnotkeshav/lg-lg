import frappe
from frappe import _
from crm.api.doc import getCounts

@frappe.whitelist()
def get_amc(name):
	if not frappe.has_permission("AMC", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	amc = frappe.get_doc("AMC", name)
	amc = amc.as_dict()
	
	# Add counts for activities
	amc = getCounts(amc, "AMC")
	
	# Get linked contacts
	amc["contacts"] = frappe.get_all(
		"CRM Contacts",
		filters={"parent": name, "parenttype": "AMC"},
		fields=["contact", "is_primary", "email", "mobile_no", "designation"]
	)
	
	# Get AMC items
	amc["items"] = frappe.get_all(
		"AMC Item",
		filters={"parent": name},
		fields=["*"]
	)
	
	return amc

@frappe.whitelist()
def get_amcs(filters=None, order_by="creation desc"):
	if not filters:
		filters = {}
		
	amcs = frappe.get_all(
		"AMC",
		filters=filters,
		fields=[
			"name", "amc_owner", "amc_type", "created_by",
			"amc_requester", "expiry_date", "customer_name",
			"phone", "email", "dealer_name", "dealer_id", "docstatus",
			"organization", "creation", "modified"
		],
		order_by=order_by
	)
	
	for amc in amcs:
		amc = getCounts(amc, "AMC")
		
	return amcs

@frappe.whitelist()
def create_amc(args):
	if not frappe.has_permission("AMC", "create"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	
	try:
		amc = frappe.get_doc({
			"doctype": "AMC",
			**frappe.parse_json(args)
		})
		amc.insert()
		
		return {
			"name": amc.name,
			"amc_owner": amc.amc_owner,
			"customer_name": amc.customer_name
		}
	except Exception as e:
		frappe.throw(str(e))

@frappe.whitelist()
def update_amc(name, args):
	if not frappe.has_permission("AMC", "write", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	try:
		amc = frappe.get_doc("AMC", name)
		amc.update(frappe.parse_json(args))
		amc.save()
		
		return amc
	except Exception as e:
		frappe.throw(str(e))

@frappe.whitelist()
def submit_amc(name):
	if not frappe.has_permission("AMC", "submit", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	amc = frappe.get_doc("AMC", name)
	amc.submit()
	
	return amc

@frappe.whitelist()
def get_organization_amcs(organization):
	if not frappe.has_permission("Organization", "read", organization):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	amcs = frappe.get_all(
		"AMC",
		filters={"organization": organization},
		fields=[
			"name", "amc_owner", "amc_type", "created_by",
			"expiry_date", "customer_name", "modified"
		],
		order_by="creation desc"
	)
	
	return amcs

@frappe.whitelist()
def get_contact_amcs(contact):
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	amc_links = frappe.get_all(
		"CRM Contacts",
		filters={"contact": contact, "parenttype": "AMC"},
		fields=["parent"],
		distinct=True
	)
	
	amcs = []
	for link in amc_links:
		amc = frappe.get_doc(
			"AMC",
			link.parent,
			fields=[
				"name", "amc_owner", "amc_type", "created_by",
				"expiry_date", "customer_name", "modified"
			]
		)
		amcs.append(amc.as_dict())
	
	return amcs

@frappe.whitelist()
def link_contact(amc, contact, is_primary=0):
	if not frappe.has_permission("AMC", "write", amc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	amc = frappe.get_doc("AMC", amc)
	
	# Check if contact already linked
	existing = list(filter(lambda x: x.contact == contact, amc.contacts))
	if existing:
		if int(is_primary):
			for contact_link in amc.contacts:
				contact_link.is_primary = 0
			existing[0].is_primary = 1
			amc.save()
		return amc
	
	# Add new contact
	amc.append("contacts", {
		"contact": contact,
		"is_primary": is_primary
	})
	amc.save()
	
	return amc

@frappe.whitelist()
def unlink_contact(amc, contact):
	if not frappe.has_permission("AMC", "write", amc):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
		
	amc = frappe.get_doc("AMC", amc)
	
	# Remove contact
	amc.contacts = [c for c in amc.contacts if c.contact != contact]
	amc.save()
	
	return amc

@staticmethod
def get_list_view_fields():
	return [
		{"label": "Name", "fieldname": "name"},
		{"label": "Customer", "fieldname": "customer_name"},
		{"label": "Organization", "fieldname": "organization"},
		{"label": "Status", "fieldname": "amc_status"},
		{"label": "Owner", "fieldname": "amc_owner"},
		{"label": "Modified", "fieldname": "modified"},
		{"label": "Comments", "fieldname": "_comments"},
		{"label": "Assigned To", "fieldname": "_assign"},
		{"label": "Modified By", "fieldname": "modified_by"}
	]

@staticmethod
def default_list_data():
	return {
		"columns": [
			{
				"label": "Name",
				"type": "Data",
				"fieldname": "name",
				"width": 200,
			},
			{
				"label": "Customer",
				"type": "Data",
				"fieldname": "customer_name",
				"width": 200,
			},
			{
				"label": "Organization",
				"type": "Link",
				"fieldname": "organization",
				"width": 200,
			},
			{
				"label": "Status",
				"type": "Select",
				"fieldname": "amc_status",
				"width": 100,
			},
			{
				"label": "Owner",
				"type": "Link",
				"fieldname": "amc_owner",
				"width": 150,
			},
			{
				"label": "Modified",
				"type": "Datetime",
				"fieldname": "modified",
				"width": 150,
			},
		],
		"fields": AMC.get_list_view_fields(),
		"rows": [
			"name",
			"customer_name",
			"organization",
			"amc_status",
			"amc_owner",
			"modified",
			"_liked_by",
			"_comments",
			"_assign",
			"modified_by"
		],
		"views": [
			{
				"label": "List",
				"name": "List",
				"view_type": "list",
			},
			{
				"label": "Kanban",
				"name": "Kanban",
				"view_type": "kanban",
			},
		],
	}

