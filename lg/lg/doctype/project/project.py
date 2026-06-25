

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class Project(Document):
    def validate(self):
        if not self.customer:
            return

        customer = frappe.get_doc("CRM Organization", self.customer)

        # Check if project already exists in child table
        exists = False
        for row in customer.project_info:
            if row.project == self.name:
                exists = True
                break

        if not exists:
            customer.append("project_info", {
                "project": self.name,
                "status": self.status,
                "expiry_date": self.expiry_date,
            })
            customer.save(ignore_permissions=True)
            frappe.db.commit()


@frappe.whitelist()
def make_crm_deal(source_name, target_doc=None):
	def set_missing_values(source, target):
		try:
			target.project = source.name
			target.organization="LGE"
			target.deal_owner = frappe.session.user
			if source.status=="AMC Expired":
				target.deal_type="Lost AMC Conversion"
			elif source.status == "OUT Warranty":
				target.deal_type = "Lost Warranty Conversion"
			if source.customer:
				customer = frappe.get_doc('CRM Organization', source.customer)
				target.branch = customer.branch
				target.region = customer.region

			
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Error in set_missing_values")
			frappe.msgprint("An error occurred while setting deal fields.")

	try:
		doclist = get_mapped_doc(
			"Project",
			source_name,
			{
				"Project": {
					"doctype": "CRM Deal",
					"field_map": {
						"customer": "customer",
						"customer_address": "customer_address",
					},
					"field_no_map":[
						"status"
					],
					"validation": {
						"docstatus": ["=", 0]
					}
				}
			},
			target_doc,
			set_missing_values,
			ignore_permissions=True
		)

		return doclist

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in make_crm_deal")
		frappe.msgprint("An error occurred while mapping Project to CRM Deal.")
