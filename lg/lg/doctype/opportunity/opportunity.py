# Copyright (c) 2024, extension and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_months, getdate
from frappe.model.document import Document

class Opportunity(Document):
    pass
@frappe.whitelist()
def get_warranty(item_code):
    if not item_code:
        frappe.throw("Item Code is required.")

    warranty_records = frappe.get_all(
        "Warranty",
        filters={"item_code": item_code},
        fields=["name", "expiry_date"]
    )
    for warranty in warranty_records:
        if warranty.get("expiry_date"):
            
            expiry_date = frappe.utils.getdate(warranty["expiry_date"])
            
            two_months_before = frappe.utils.add_months(expiry_date, -2)
           
            warranty["two_months_before"] = two_months_before
    return warranty_records

