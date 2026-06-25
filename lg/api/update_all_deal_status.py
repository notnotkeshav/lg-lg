import frappe
from frappe.utils import getdate, today

def update_all_deal_statuses():
    current_date = getdate(today())
    deals = frappe.get_all("CRM Deal", fields=["name", "amc_expiry_date", "warranty_expiry_date"])

    for deal in deals:
        # Skip if no expiry date at all
        if not deal.amc_expiry_date and not deal.warranty_expiry_date:
            continue  # ⛔ Skip this deal
        doc = frappe.get_doc("CRM Deal", deal.name)
        previous_status = doc.warranty_amc_status

        if doc.amc_expiry_date:
            expiry = getdate(doc.amc_expiry_date)
            doc.warranty_amc_status = "AMC Active" if expiry > current_date else "AMC Expired"
        elif doc.warranty_expiry_date:
            expiry = getdate(doc.warranty_expiry_date)
            doc.warranty_amc_status = "IN Warranty" if expiry > current_date else "OUT Warranty"

        # Only save if status changed
        if doc.warranty_amc_status != previous_status:
            doc.save(ignore_permissions=True)  # This will trigger on_update
