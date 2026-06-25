# Copyright (c) 2026, extension and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import nowdate

class AMCTerm(Document):
	pass

# @frappe.whitelist()
# def make_crm_contract(source_name, target_doc=None):
# 	def set_missing_values(source, target):
# 		target.date = frappe.utils.nowdate()
# 		target.status = "Draft"
# 		target.naming_series = "CNT-.YYYY.-"

# 	doclist = get_mapped_doc(
# 		"AMC Term",
# 		source_name,
# 		{
# 			"AMC Term": {
# 				"doctype": "CRM Contract",
# 				"field_map": {
# 					"payment_term": "payment_term",
# 					"end_date": "expiry_date",
# 					"start_date": "start_date",
# 					"amount":"amount",
# 					"payment_frequency":"payment_frequency",
# 					"billing_terms":"billing_terms",
# 					"billing_schedule":"billing_schedule"


# 				},

# 			},
# 		},
# 		target_doc,
# 		set_missing_values
# 	)
# 	return doclist 


@frappe.whitelist()
def make_crm_contract(source_name, target_doc=None):
    # 1. Pehle AMC Term (source) ko load karein taaki hum reference_contract ki ID le sakein
    amc_term = frappe.get_doc("AMC Term", source_name)
    
    # 2. Agar reference_contract hai, toh us purane contract ka data fetch karein
    old_contract_data = None
    if amc_term.reference_contract:
        old_contract_data = frappe.get_doc("CRM Contract", amc_term.reference_contract)

    def set_missing_values(source, target):
        target.date = frappe.utils.nowdate()
        target.status = "Draft"
        target.naming_series = "CNT-.YYYY.-"
        
        # 3. Yahan hum purane contract se values map karenge
        if old_contract_data:
            target.customer = old_contract_data.customer
            target.customer_name = old_contract_data.customer_name
            target.industry = old_contract_data.industry
            target.region = old_contract_data.region
            target.branch = old_contract_data.branch
            target.company = old_contract_data.company

            # Agar koi aur field bhi chahiye toh yahan add kar sakte hain
            # target.fieldname = old_contract_data.fieldname

    doclist = get_mapped_doc(
        "AMC Term",
        source_name,
        {
            "AMC Term": {
                "doctype": "CRM Contract",
                "field_map": {
                    "payment_term": "payment_term",
                    "end_date": "expiry_date",
                    "start_date": "start_date",
                    "amount": "amount",
                    "payment_frequency": "payment_frequency",
                    "billing_terms": "billing_terms",
                },
            },
        },
        target_doc,
        set_missing_values
    )
    return doclist

