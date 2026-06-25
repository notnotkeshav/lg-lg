# Copyright (c) 2025, extension and contributors
# For license information, please see license.txt
# password - WJGclOo5l5VM8RA

import frappe
from frappe.utils import nowdate, date_diff

def execute(filters=None):
    if not filters:
        filters = {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Name", "fieldname": "name", "fieldtype": "Link", "options": "CRM Contract", "width": 200},
        {"label": "0–30 Days", "fieldname": "range1", "fieldtype": "Currency", "width": 120},
        {"label": "31–60 Days", "fieldname": "range2", "fieldtype": "Currency", "width": 120},
        {"label": "61–90 Days", "fieldname": "range3", "fieldtype": "Currency", "width": 120},
        {"label": "90+ Days", "fieldname": "range4", "fieldtype": "Currency", "width": 120},
        {"label": "Total Amount", "fieldname": "total", "fieldtype": "Currency", "width": 150},
    ]

def get_data(filters):
    today = nowdate()

    # Fetch required fields — include payment_date <html> g
    contracts = frappe.db.sql("""
          SELECT 
            c.name as name, 
            c.amount as amount, 
            c.branch as branch,
            c.customer_name as customer_name,
            c.project as project,
            b.payment_date as payment_date
        FROM `tabCRM Contract` AS c
        LEFT JOIN `tabContract Billing Schedule` AS b 
            ON b.parent = c.name
        WHERE c.amount > 0
    """, as_dict=True)

    data = {}

    for con in contracts:
        # Skip records missing expiry_date
        if not con.expiry_date:
            continue

        age = date_diff(today, con.payment_date)
        name = con.name or "Unassigned"

        if name not in data:
            data[name] = {
                "name": name,
                "range1": 0,
                "range2": 0,
                "range3": 0,
                "range4": 0,
                "total": 0
            }

        if age <= 30:
            data[name]["range1"] += con.amount
        elif age <= 60:
            data[name]["range2"] += con.amount
        elif age <= 90:
            data[name]["range3"] += con.amount
        else:
            data[name]["range4"] += con.amount

        data[name]["total"] += con.amount

    return list(data.values())
