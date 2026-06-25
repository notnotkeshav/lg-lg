# Copyright (c) 2025, extension and contributors
# For license information, please see license.txt

import frappe
from __future__ import unicode_literals
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

def execute(filters=None):
    columns = get_columns()
    data = []

    if not filters:
        return columns, data

    today = date.today()

    # Determine end date based on period type
    if filters.get("period_type") == "Days":
        end_date = today + timedelta(days=int(filters.get("days_value", 0)))
    elif filters.get("period_type") == "Months":
        end_date = today + relativedelta(months=int(filters.get("months_value", 0)))
    else:
        end_date = today

    # Fetch data
    data = frappe.db.sql("""
        SELECT 
            name AS Contract,
            expiry_date AS `Expiry Date`,
            total_hp AS `Total HP`
        FROM 
            `tabCRM Contract`
        WHERE 
            expiry_date > %s AND expiry_date <= %s
        ORDER BY expiry_date
    """, (today, end_date), as_dict=True)

    return columns, data

def get_columns():
    return [
        {"label": "Contract", "fieldname": "Contract", "fieldtype": "Link", "options": "CRM Contract", "width": 200},
        {"label": "Expiry Date", "fieldname": "Expiry Date", "fieldtype": "Date", "width": 120},
        {"label": "Total HP", "fieldname": "Total HP", "fieldtype": "Float", "width": 100}
    ]

