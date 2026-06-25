# Copyright (c) 2024, extension and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe
from frappe import _
from crm.api.doc import getCounts

class Warranty(Document):
    @frappe.whitelist()
    def get_warranty(name):
        if not frappe.has_permission("Warranty", "read", name):
            frappe.throw(_("Not permitted"), frappe.PermissionError)
            
        warranty = frappe.get_doc("Warranty", name)
        warranty = warranty.as_dict()
        
        # Add counts for activities
        warranty = getCounts(warranty, "Warranty")
        
        # Get linked contacts
        warranty["contacts"] = frappe.get_all(
            "CRM Contacts",
            filters={"parent": name, "parenttype": "Warranty"},
            fields=["contact", "is_primary", "email", "mobile_no", "designation"]
        )
        
        # Get warranty items
        warranty["items"] = frappe.get_all(
            "Warranty Item",
            filters={"parent": name},
            fields=["*"]
        )
        
        return warranty

    @frappe.whitelist()
    def get_warranties(filters=None, order_by="creation desc"):
        if not filters:
            filters = {}
            
        warranties = frappe.get_all(
            "Warranty",
            filters=filters,
            fields=[
                "name", "warranty_owner", "warranty_type", "created_by",
                "warranty_requester", "expiry_date", "customer_name",
                "phone", "email", "dealer_name", "dealer_id", "docstatus",
                "organization", "creation", "modified"
            ],
            order_by=order_by
        )
        
        for warranty in warranties:
            warranty = getCounts(warranty, "Warranty")
            
        return warranties

    @frappe.whitelist()
    def create_warranty(args):
        if not frappe.has_permission("Warranty", "create"):
            frappe.throw(_("Not permitted"), frappe.PermissionError)
        
        try:
            warranty = frappe.get_doc({
                "doctype": "Warranty",
                **frappe.parse_json(args)
            })
            warranty.insert()
            
            return {
                "name": warranty.name,
                "warranty_owner": warranty.warranty_owner,
                "customer_name": warranty.customer_name
            }
        except Exception as e:
            frappe.throw(str(e))

    @frappe.whitelist()
    def update_warranty(name, args):
        if not frappe.has_permission("Warranty", "write", name):
            frappe.throw(_("Not permitted"), frappe.PermissionError)
            
        try:
            warranty = frappe.get_doc("Warranty", name)
            warranty.update(frappe.parse_json(args))
            warranty.save()
            
            return warranty
        except Exception as e:
            frappe.throw(str(e))

    @frappe.whitelist()
    def submit_warranty(name):
        if not frappe.has_permission("Warranty", "submit", name):
            frappe.throw(_("Not permitted"), frappe.PermissionError)
            
        warranty = frappe.get_doc("Warranty", name)
        warranty.submit()
        
        return warranty

    @frappe.whitelist()
    def get_organization_warranties(organization):
        if not frappe.has_permission("Organization", "read", organization):
            frappe.throw(_("Not permitted"), frappe.PermissionError)
            
        warranties = frappe.get_all(
            "Warranty",
            filters={"organization": organization},
            fields=[
                "name", "warranty_owner", "warranty_type", "created_by",
                "expiry_date", "customer_name", "modified"
            ],
            order_by="creation desc"
        )
        
        return warranties

    @frappe.whitelist()
    def get_contact_warranties(contact):
        if not frappe.has_permission("Contact", "read", contact):
            frappe.throw(_("Not permitted"), frappe.PermissionError)
            
        warranty_links = frappe.get_all(
            "CRM Contacts",
            filters={"contact": contact, "parenttype": "Warranty"},
            fields=["parent"],
            distinct=True
        )
        
        warranties = []
        for link in warranty_links:
            warranty = frappe.get_doc(
                "Warranty",
                link.parent,
                fields=[
                    "name", "warranty_owner", "warranty_type", "created_by",
                    "expiry_date", "customer_name", "modified"
                ]
            )
            warranties.append(warranty.as_dict())
        
        return warranties

    @frappe.whitelist()
    def link_contact(warranty, contact, is_primary=0):
        if not frappe.has_permission("Warranty", "write", warranty):
            frappe.throw(_("Not permitted"), frappe.PermissionError)
            
        warranty = frappe.get_doc("Warranty", warranty)
        
        # Check if contact already linked
        existing = list(filter(lambda x: x.contact == contact, warranty.contacts))
        if existing:
            if int(is_primary):
                for contact_link in warranty.contacts:
                    contact_link.is_primary = 0
                existing[0].is_primary = 1
                warranty.save()
            return warranty
        
        # Add new contact
        warranty.append("contacts", {
            "contact": contact,
            "is_primary": is_primary
        })
        warranty.save()
        
        return warranty

    @frappe.whitelist()
    def unlink_contact(warranty, contact):
        if not frappe.has_permission("Warranty", "write", warranty):
            frappe.throw(_("Not permitted"), frappe.PermissionError)
            
        warranty = frappe.get_doc("Warranty", warranty)
        
        # Remove contact
        warranty.contacts = [c for c in warranty.contacts if c.contact != contact]
        warranty.save()
        
        return warranty

    @staticmethod
    def get_list_view_fields():
        return [
            {"label": "Name", "fieldname": "name"},
            {"label": "Customer", "fieldname": "customer_name"},
            {"label": "Organization", "fieldname": "organization"},
            {"label": "Status", "fieldname": "warranty_status"},
            {"label": "Owner", "fieldname": "warranty_owner"},
            {"label": "Modified", "fieldname": "modified"},
            {"label": "Comments", "fieldname": "_comments"},
            {"label": "Assigned To", "fieldname": "_assign"},
            {"label": "Modified By", "fieldname": "modified_by"}
        ]

    @staticmethod
    def default_list_data():
        return {
            "columns": [
                {
                    "label": "Name",
                    "type": "Data",
                    "fieldname": "name",
                    "width": 200,
                },
                {
                    "label": "Customer",
                    "type": "Data",
                    "fieldname": "customer_name",
                    "width": 200,
                },
                {
                    "label": "Organization",
                    "type": "Link",
                    "fieldname": "organization",
                    "width": 200,
                },
                {
                    "label": "Status",
                    "type": "Select",
                    "fieldname": "warranty_status",
                    "width": 100,
                },
                {
                    "label": "Owner",
                    "type": "Link",
                    "fieldname": "warranty_owner",
                    "width": 150,
                },
                {
                    "label": "Modified",
                    "type": "Datetime",
                    "fieldname": "modified",
                    "width": 150,
                },
            ],
            "fields": Warranty.get_list_view_fields(),
            "rows": [
                "name",
                "customer_name",
                "organization",
                "warranty_status",
                "warranty_owner",
                "modified",
                "_liked_by",
                "_comments",
                "_assign",
                "modified_by"
            ],
            "views": [
                {
                    "label": "List",
                    "name": "List",
                    "view_type": "list",
                },
                {
                    "label": "Kanban",
                    "name": "Kanban",
                    "view_type": "kanban",
                },
            ],
        }