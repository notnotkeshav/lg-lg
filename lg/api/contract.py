import frappe
from frappe import _
from frappe.utils import cint
from crm.api.doc import get_fields_meta, get_assigned_users
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script

@frappe.whitelist()
def get_contract(name):
    """Get contract details"""
    Contract = frappe.qb.DocType("CRM Contract")

    query = (
        frappe.qb.from_(Contract)
        .select("*")
        .where(Contract.name == name)
        .limit(1)
    )

    contract = query.run(as_dict=True)
    if not len(contract):
        frappe.throw(_("Contract not found"), frappe.DoesNotExistError)
    contract = contract.pop()

    contract["doctype"] = "CRM Contract"
    contract["fields_meta"] = get_fields_meta("CRM Contract")
    contract["_form_script"] = get_form_script('CRM Contract')
    contract["_assign"] = get_assigned_users("CRM Contract", contract.name, contract.owner)
    return contract

@frappe.whitelist()
def get_contracts(filters=None, fields=None, order_by=None, start=0, page_length=20):
    """Get list of contracts"""
    if filters is None:
        filters = {}
    if fields is None:
        fields = [
            "name",
            "title",
            "customer",
            "customer_name",
            "date",
            "status",
            "contract_items",
            "modified",
            "_assign",
            "_liked_by",
            "_comments"
        ]
    if order_by is None:
        order_by = "modified desc"

    contracts = frappe.get_list(
        "CRM Contract",
        filters=filters,
        fields=fields,
        order_by=order_by,
        start=start,
        page_length=page_length
    )
    return contracts

@frappe.whitelist()
def create_contract(contract_data):
    """Create a new contract"""
    if isinstance(contract_data, str):
        contract_data = frappe.parse_json(contract_data)

    contract = frappe.new_doc("CRM Contract")
    contract.update(contract_data)
    contract.insert()
    return contract.name

@frappe.whitelist()
def update_contract(name, contract_data):
    """Update contract"""
    if isinstance(contract_data, str):
        contract_data = frappe.parse_json(contract_data)

    contract = frappe.get_doc("CRM Contract", name)
    contract.update(contract_data)
    contract.save()
    return contract.as_dict()

@frappe.whitelist()
def delete_contract(name):
    """Delete contract"""
    frappe.delete_doc("CRM Contract", name)
    return True

@frappe.whitelist()
def submit_contract(name):
    """Submit contract"""
    contract = frappe.get_doc("CRM Contract", name)
    contract.submit()
    return contract.as_dict()

@frappe.whitelist()
def cancel_contract(name):
    """Cancel contract"""
    contract = frappe.get_doc("CRM Contract", name)
    contract.cancel()
    return contract.as_dict()

@frappe.whitelist()
def get_customer(customer):
    """Get customer details"""
    customer_doc = frappe.get_doc("Customer", customer)
    return {
        "customer_name": customer_doc.customer_name,
        "customer_hc": customer_doc.customer_hc
    }

@frappe.whitelist()
def get_serial_numbers(query=None):
    """Get list of serial numbers"""
    filters = {}
    if query:
        filters["name"] = ["like", f"%{query}%"]
    
    return frappe.get_list(
        "Serial No",
        filters=filters,
        fields=["name as value", "name as label"],
        limit=10
    )

@frappe.whitelist()
def get_serial_details(serial_no):
    """Get serial number details"""
    serial = frappe.get_doc("Serial No", serial_no)
    return {
        "product_code": serial.product_code,
        "product_name": serial.product_name
    }