# warranty_management/api/list.py
import frappe
import json

@frappe.whitelist()
def save_column_preferences(columns):
    user = frappe.session.user
    frappe.db.set_value(
        'User',
        user,
        'warranty_list_columns',
        json.dumps(columns)
    )
    return True

@frappe.whitelist()
def get_column_preferences():
    user = frappe.session.user
    columns = frappe.db.get_value(
        'User',
        user,
        'warranty_list_columns'
    )
    return json.loads(columns) if columns else None