import frappe
from frappe import _
import json

from crm.api.doc import get_fields_meta, get_assigned_users
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script

@frappe.whitelist()
def get_contract(name):
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
def get_contract_contacts(name):
    contacts = frappe.get_all(
        "CRM Contacts",
        filters={"parenttype": "CRM Contract", "parent": name},
        fields=["contact", "is_primary"],
    )
    contract_contacts = []
    for contact in contacts:
        is_primary = contact.is_primary
        contact = frappe.get_doc("Contact", contact.contact).as_dict()
        def get_primary_email(contact):
            for email in contact.email_ids:
                if email.is_primary:
                    return email.email_id
            return contact.email_ids[0].email_id if contact.email_ids else ""
        def get_primary_mobile_no(contact):
            for phone in contact.phone_nos:
                if phone.is_primary:
                    return phone.phone
            return contact.phone_nos[0].phone if contact.phone_nos else ""
        _contact = {
            "name": contact.name,
            "image": contact.image,
            "full_name": contact.full_name,
            "email": get_primary_email(contact),
            "mobile_no": get_primary_mobile_no(contact),
            "is_primary": is_primary,
        }
        contract_contacts.append(_contact)
    return contract_contacts

@frappe.whitelist()
def add_contact(contract, contact):
    doc = frappe.get_doc("CRM Contract", contract)
    doc.append("contacts", {"contact": contact})
    doc.save()
    return True

@frappe.whitelist()
def remove_contact(contract, contact):
    doc = frappe.get_doc("CRM Contract", contract)
    for row in doc.contacts:
        if row.contact == contact:
            doc.remove(row)
            break
    doc.save()
    return True

@frappe.whitelist()
def set_primary_contact(contract, contact):
    doc = frappe.get_doc("CRM Contract", contract)
    for row in doc.contacts:
        row.is_primary = 1 if row.contact == contact else 0
    doc.save()
    return True 