# Copyright (c) 2024, extension and contributors
# For license information, please see license.txt

# import frappe

import json

import frappe
from frappe import _
from frappe.model.document import Document

# crm.setup.doctype.serial_no.serial_no.create_serial
# crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout

class SerialNo(Document):
	pass

@frappe.whitelist()
def create_serial(args):
	serial = frappe.new_doc("Serial No")

	serial.update({
		"serial_no": args.get("serial_no") ,
		"product_name":args.get("product_name"),
		"product_group":args.get("product_group"),
		"start_date":args.get("start_date"),
		"expiry_date":args.get("expiry_date"),
		"status":args.get("status"),
		"type":args.get("type"),
		"warranty_period_in_days":args.get("warranty_period_in_days")

	})

	args.pop("serial_no", None)

	serial.update(args)

	serial.insert(ignore_permissions=True)
	return serial.name

