import frappe
from frappe import _
import json

from crm.api.doc import get_fields_meta, get_assigned_users
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script

@frappe.whitelist()
def get_quotation(name):
    """Get quotation details"""
    try:
        quotation = frappe.get_doc('CRM Quotation', name)
        return quotation
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _('Error fetching quotation'))
        frappe.throw(_('Could not fetch quotation: {0}').format(str(e)))

@frappe.whitelist()
def get_fields_layout(name=None):
    """Get the fields layout for the quotation form"""
    try:
        fields_to_exclude = ['naming_series', 'amended_from', 'owner', 'creation', 'modified', 'modified_by']
        
        meta = frappe.get_meta('CRM Quotation')
        fields = [f for f in meta.fields if f.fieldname not in fields_to_exclude]
        
        sections = [
            {
                "label": _("Basic Information"),
                "fields": [f for f in fields if f.fieldname in [
                    'customer', 'customer_hc', 'date', 'valid_till', 'status'
                ]]
            },
            {
                "label": _("Product Details"),
                "fields": [f for f in fields if f.fieldname in [
                    'deal_type', 'serial_no', 'product_name'
                ]]
            },
            {
                "label": _("Pricing Information"),
                "fields": [f for f in fields if f.fieldname in [
                    'amc', 'currency', 'amount', 'payment_frequency',
                    'price_list_currency', 'price_list_exchange_rate',
                    'conversion_rate'
                ]]
            },
            {
                "label": _("Taxes and Charges"),
                "fields": [f for f in fields if f.fieldname in [
                    'tax_category', 'sales_taxes_and_charges_template',
                    'total_taxes_and_charges_inr', 'grand_total_inr',
                    'rounded_total_inr'
                ]]
            },
            {
                "label": _("Additional Discount"),
                "fields": [f for f in fields if f.fieldname in [
                    'apply_additional_discount_on', 'additional_discount_percentage',
                    'additional_discount_amount_inr'
                ]]
            },
            {
                "label": _("Billing Address"),
                "fields": [f for f in fields if f.fieldname in [
                    'customer_address', 'address_line_1', 'address_line_2',
                    'city', 'state', 'country', 'pincode', 'mobile_no',
                    'contact_email', 'billing_address_gstin', 'gst_category',
                    'place_of_supply'
                ]]
            },
            {
                "label": _("Shipping Address"),
                "fields": [f for f in fields if f.fieldname in [
                    'shipping_address', 'shipping_address_line_1',
                    'shipping_address_line_2', 'shipping_city', 'shipping_state',
                    'shipping_pincode', 'shipping_phone', 'shipping_email'
                ]]
            },
            {
                "label": _("Terms and Conditions"),
                "fields": [f for f in fields if f.fieldname in [
                    'payment_terms', 'terms', 'term_details'
                ]]
            }
        ]
        
        # Add field values if name is provided
        if name:
            doc = frappe.get_doc('CRM Quotation', name)
            for section in sections:
                for field in section['fields']:
                    field.value = doc.get(field.fieldname)
                    
                    # Add special handling for certain fields
                    if field.fieldname == 'status':
                        field.type = 'Select'
                        field.options = frappe.get_meta('CRM Quotation').get_field('status').options
                    elif field.fieldname in ['customer', 'customer_address', 'shipping_address']:
                        field.type = 'Link'
                        field.options = field.options or 'CRM Organization'
        
        # Filter out empty sections
        sections = [section for section in sections if section['fields']]
        
        return sections
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _('Error fetching fields layout'))
        frappe.throw(_('Could not fetch fields layout: {0}').format(str(e)))

@frappe.whitelist()
def get_quotation_contacts(name):
    """Get contacts linked to the quotation"""
    try:
        quotation = frappe.get_doc('CRM Quotation', name)
        contacts = []
        if quotation.customer:
            contacts = frappe.get_all(
                'Contact',
                filters={'company_name': quotation.customer},
                fields=['name', 'first_name', 'last_name', 'email_id', 'mobile_no', 'is_primary_contact']
            )
            for contact in contacts:
                contact.full_name = ' '.join(filter(None, [contact.first_name, contact.last_name]))
                contact.is_primary = contact.is_primary_contact
                contact.email = contact.email_id
                contact.mobile_no = contact.mobile_no
        return contacts
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _('Error fetching quotation contacts'))
        frappe.throw(_('Could not fetch contacts: {0}').format(str(e)))

@frappe.whitelist()
def delete_quotation(name):
    """Delete a quotation"""
    try:
        frappe.delete_doc('CRM Quotation', name)
        return True
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _('Error deleting quotation'))
        frappe.throw(_('Could not delete quotation: {0}').format(str(e)))

@frappe.whitelist()
def add_contact(quotation, contact):
    doc = frappe.get_doc("CRM Quotation", quotation)
    doc.append("contacts", {"contact": contact})
    doc.save()
    return True

@frappe.whitelist()
def remove_contact(quotation, contact):
    doc = frappe.get_doc("CRM Quotation", quotation)
    for row in doc.contacts:
        if row.contact == contact:
            doc.remove(row)
            break
    doc.save()
    return True

@frappe.whitelist()
def set_primary_contact(quotation, contact):
    doc = frappe.get_doc("CRM Quotation", quotation)
    for row in doc.contacts:
        row.is_primary = 1 if row.contact == contact else 0
    doc.save()
    return True 