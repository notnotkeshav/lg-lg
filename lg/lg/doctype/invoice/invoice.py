# Copyright (c) 2025, extension and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_days, cint, nowdate

class Invoice(Document):
    pass

def update_invoice_outstanding_per_portion():
    today = getdate(nowdate())

    invoices = frappe.get_all(
        "Invoice",
        filters={"status": ["!=", "Paid"]},
        fields=["name"]
    )

    for inv in invoices:
        invoice_doc = frappe.get_doc("Invoice", inv.name)
        updated = False

        for term in invoice_doc.get("invoice_payment_term") or []:
            due_date = term.due_date
            if due_date and getdate(due_date) < today:
                portion_amount = flt(term.portion_amount or 0)
                amount_received = flt(term.amount_received or 0)
                outstanding = portion_amount - amount_received

                if term.outstanding_as_per_portion != outstanding:
                    term.outstanding_as_per_portion = outstanding
                    updated = True

        if updated:
            invoice_doc.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.log(f"Updated outstanding_as_per_portion for Invoice: {invoice_doc.name}")

@frappe.whitelist()
def update_due_dates_from_posting(invoice_id, posting_date=None):
    invoice = frappe.get_doc("Invoice", invoice_id)
    base_date = getdate(posting_date or invoice.posting_date)

    if not invoice.posting_date:
        frappe.throw("Posting Date is not set in Invoice")

    if not invoice.pay_term:
        frappe.throw(f"No Pay Term found for Invoice {invoice.name}")

    pay_term = frappe.get_doc("Pay Term", invoice.pay_term)

    if not pay_term.payment_term_portions:
        frappe.throw(f"No Payment Term Portions found in Pay Term {pay_term.name}")

    updated_rows = []

    for idx, portion in enumerate(pay_term.payment_term_portions):
        days = cint(portion.days or 0)
        due_date = add_days(base_date, days)

        if invoice.invoice_payment_term and idx < len(invoice.invoice_payment_term):
            inv_term = invoice.invoice_payment_term[idx]
            frappe.db.set_value("Invoice Payment Term", inv_term.name, "due_date", due_date)
            updated_rows.append({
                "term_row": inv_term.name,
                "portion": portion.invoice_portion,
                "days": days,
                "due_date": due_date
            })

    frappe.db.commit()
    return {
        "message": f"✅ Updated due dates for {len(updated_rows)} term(s) in Invoice {invoice.name}",
        "updated_terms": updated_rows
    }
