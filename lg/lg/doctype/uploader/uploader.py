import frappe
from frappe.model.document import Document



from frappe.utils import today, add_days, flt,nowdate


class Uploader(Document):
    def after_insert(doc, method=None):
        try:
            

            today = getdate(nowdate())  # call nowdate() to get string, then getdate() to convert to date

            frappe.log_error(message="Uploader after_insert started", title="Uploader Log")

            # Process invoice_uploader if upload type is "Invoice"
            if doc.upload == "Invoice":
                if doc.get("invoice_uploader"):
                    for row in doc.get("invoice_uploader"):
                        if not row.contract_id:
                            frappe.log_error(message=f"Skipping row with no contract_id: {row.as_dict()}", title="Uploader Log")
                            continue  # Skip if contract not linked

                        # 🛑 Skip if Invoice with same invoice_id already exists
                        if row.invoice_id and frappe.db.exists("Invoice", {"invoice": row.invoice_id}):
                            frappe.log_error(message=f"Skipping duplicate Invoice: {row.invoice_id}", title="Uploader Log")
                            continue

                        frappe.log_error(message=f"Processing invoice_uploader row: {row.as_dict()}", title="Uploader Log")

                        # Fetch related Contract
                        contract = frappe.get_doc("CRM Contract", row.contract_id)
                        start_date = contract.start_date
                        end_date = contract.expiry_date
                        pay_term = contract.payment_term
                        total_billed = flt(row.amount)
                        posting_date = row.billed_date

                        # Create new Invoice document
                        payment_doc = frappe.new_doc("Invoice")
                        payment_doc.amc_contract_id = row.contract_id
                        payment_doc.amc_start_date = start_date
                        payment_doc.amc_end_date = end_date
                        payment_doc.posting_date = posting_date
                        payment_doc.invoice = row.invoice_id
                        payment_doc.status = "Invoice Raised"
                        payment_doc.pay_term = pay_term
                        payment_doc.amount_invoiced = row.amount

                        # Append payment term portions if payment_term exists
                        if contract.payment_term:
                            payment_term_doc = frappe.get_doc("Pay Term", contract.payment_term)
                            payment_portions = payment_term_doc.get("payment_term_portions") or []
                            payment_portions_sorted = sorted(payment_portions, key=lambda x: flt(x.get("days") or 0))

                            for t in payment_portions_sorted:
                                invoice_portion = flt(t.get("invoice_portion") or 0)
                                days = int(t.get("days") or 0)
                                portion_amount = (total_billed * invoice_portion) / 100
                                due_date = add_days(posting_date, days)

                                payment_doc.append("invoice_payment_term", {
                                    "portion": invoice_portion,
                                    "due_date": due_date,
                                    "portion_amount": portion_amount,
                                })

                        payment_doc.insert(ignore_permissions=True)
                        frappe.log_error(message=f"Inserted Invoice: {payment_doc.name}", title="Uploader Log")

                        # Update matching Contract Billing Schedule row
                        for sched in contract.get("billing_schedule") or []:
                            sched_amount = flt(sched.amount)
                            sched_date = str(sched.billing_date)
                            uploader_date = str(row.billing_date)
                            uploader_amount = flt(row.amount)

                            if sched_date == uploader_date and sched_amount == uploader_amount:
                                frappe.db.set_value(
                                    "Contract Billing Schedule",
                                    sched.name, {
                                        "invoice_id": row.invoice_id,
                                        "billed_date": posting_date,
                                        "status": "Invoice Raised",
                                        "invoice_link":payment_doc.name
                                    }
                                )
                                frappe.log_error(message=f"Updated Contract Billing Schedule: {sched.name} with invoice_id {row.invoice_id}", title="Uploader Log")
                                break

                else:
                    frappe.log_error(message="No invoice_uploader found, skipping invoice creation", title="Uploader Log")

            # Process payment_uploader if upload type is "Payment"
            elif doc.upload == "Payment":
                frappe.log_error(message="Processing payment_uploader child table", title="Uploader Log")
                if doc.get("payment_uploader"):

                    for payment_row in doc.get("payment_uploader") or []:
                        invoice_id = payment_row.invoice_id
                        payment_received_date = payment_row.payment_received_date
                        received_amount = payment_row.amount_received
                        total_amount = payment_row.amount
                        frappe.log_error("total amount of uploader",total_amount)
                        frappe.log_error("Amount recive in uplodaer",received_amount)
                        payment_id = payment_row.payment_id

                        frappe.log_error(message=f"Payment amount in uploader: {received_amount}", title="Uploader Debug")

                        if not invoice_id:
                            frappe.log_error(message="Skipping payment_row with no invoice_id", title="Uploader Log")
                            continue

                        invoice_doc = frappe.get_all("Invoice", filters={"name": invoice_id}, limit=1)
                        if not invoice_doc:
                            frappe.log_error(message=f"No Invoice found with name: {invoice_id}", title="Uploader Log")
                            continue

                        inv = frappe.get_doc("Invoice", invoice_doc[0].name)

                        try:
                            # Update child rows explicitly and save parent doc
                            for term in inv.get("invoice_payment_term") or []:
                                due_date = term.due_date
                                frappe.log_error("due date",due_date)
                                invoice_total_amount = term.portion_amount
                                frappe.log_error("invoice portiaon amout",invoice_total_amount)
                                if due_date and getdate(due_date) <= today and total_amount ==  invoice_total_amount:
                                    frappe.log_error("working under invoice")
                                    term.amount_received = (term.amount_received or 0) + received_amount
                                    term.amount_received_date = payment_received_date
                                    term.payment_id = payment_id
                                    term.outstanding_as_per_portion = term.portion_amount - term.amount_received
                                    term.db_update()  # persist child row update
                                    frappe.log_error(message=f"Updated payment in invoice_payment_term row: {term.name} with amount {term.amount_received}", title="Uploader Debug")
                            # *** Update parent Invoice fields here based on child rows ***
                            total_received = sum(term.amount_received or 0 for term in inv.get("invoice_payment_term") or [])

                            inv.total_paid = total_received
                            total_outstanding = inv.amount_invoiced - total_received
                            inv.total_outstanding = total_outstanding
                            if inv.amount_invoiced  == total_received:
                                inv.status = "Paid"
                            else:
                                inv.status = "Partially Paid"

                            invoice_status = inv.status  # save for later use
                            inv.save(ignore_permissions=True)
                            frappe.log_error(message=f"Saved Invoice {inv.name} after updating payment terms", title="Uploader Log")
                        except Exception as e:
                            frappe.log_error(message=f"Error saving Invoice {inv.name}: {str(e)}", title="Uploader Log")

                        # Update Contract Billing Schedule
                        child_rows = frappe.get_all(
                            "Contract Billing Schedule",
                            filters={"parent": payment_row.contract_id, "invoice_id": invoice_id},
                            fields=["name"]
                        )

                        if child_rows:
                            row_name = child_rows[0].name
                            frappe.db.set_value(
                                "Contract Billing Schedule",
                                row_name,
                                "status",
                                invoice_status
                            )
                            frappe.log_error(message=f"Updated Contract Billing Schedule {row_name} with payment data", title="Uploader Log")
                        else:
                            frappe.log_error(message=f"No Contract Billing Schedule found for contract {payment_row.contract_id} and invoice {invoice_id}", title="Uploader Log")

            else:
                frappe.log_error(message=f"Unknown upload type: {doc.upload}, skipping processing", title="Uploader Log")

            frappe.db.commit()
            frappe.log_error(message="Uploader after_insert completed successfully", title="Uploader Log")

        except Exception as e:
            frappe.log_error(message=frappe.get_traceback(), title="Uploader after_insert Error")
            frappe.throw(f"Error while processing Uploader: {str(e)}")



import frappe
from frappe.utils import getdate

@frappe.whitelist()
def get_invoice_upload_data():
    """Return invoice upload data for current month"""
    from datetime import date

    today = date.today()
    current_month = today.month
    current_year = today.year

    data = []

    # Get all active contracts
    contracts = frappe.get_all(
        "CRM Contract",
        filters={"custom_contract_status": "Active"},
        fields=["name", "customer", "project", "bill_ship_code"]
    )

    for contract in contracts:
        contract_doc = frappe.get_doc("CRM Contract", contract.name)
        for sched in contract_doc.get("billing_schedule") or []:
            billing_date = getdate(sched.billing_date)
            if (
                billing_date.month <= current_month
                and billing_date.year <= current_year
                and sched.status == "Pending"
            ):
                data.append({
                    "contract_id": contract.name,
                    "customer": contract.customer,
                    "project": contract.project,
                    "billing_date": sched.billing_date,
                    "amount": sched.amount,
                    "bill_ship_code": contract.bill_ship_code
                })

    return data


import frappe
from frappe.utils import getdate, nowdate


@frappe.whitelist()
def get_payment_upload_data():
    """Return invoices whose due date (from invoice_payment_term) is today or earlier,
    enriched with customer, bill_ship_code, and billing_term from the related Contract."""
    from frappe.utils import getdate, nowdate, flt
    import frappe

    today = getdate(nowdate())
    payment_data = []

    # Fetch all invoices (parent fields only)
    invoices = frappe.get_all(
        "Invoice",
        fields=["name", "invoice", "amc_contract_id", "amount_invoiced", "status"]
    )

    for inv in invoices:
        inv_doc = frappe.get_doc("Invoice", inv.name)

        # ✅ Loop through each invoice_payment_term child row
        for term in inv_doc.get("invoice_payment_term") or []:
            due_date = term.get("due_date")
            portion_amount=term.get("portion_amount")
            outstanding_amount =term.get("outstanding_as_per_portion")
            payment_id = term.get("payment_id")
            amount_received = flt(term.get("amount_received") or 0)

            # ✅ Match if due date is today or earlier
            if due_date and getdate(due_date) <= today and portion_amount!= amount_received:
                customer = ""
                bill_ship_code = ""
                billing_term = ""

                # ✅ If linked contract exists, get customer, bill_ship_code, and matching billing_term
                if inv.amc_contract_id:
                    contract = frappe.get_doc("CRM Contract", inv.amc_contract_id)
                    customer = contract.customer
                    bill_ship_code = contract.bill_ship_code

                    # Find billing schedule row with "Invoice Raised" status
                    for sched in contract.get("billing_schedule") or []:
                        if sched.status == "Invoice Raised":
                            billing_term = sched.billing_term
                            break

                # ✅ Append enriched data
                payment_data.append({
                    "invoice_id": inv.invoice,
                    "contract_id": inv.amc_contract_id,
                    "customer": customer,
                    "bill_ship_code": bill_ship_code,
                    "billing_term": billing_term,
                    "amount": portion_amount,
                    "outstanding_amount":outstanding_amount,
                    "status": inv.status,
                    "due_date": due_date,
                    "payment_id":payment_id
                })
                break  # Include each invoice once

    return payment_data
