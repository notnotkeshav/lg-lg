# Copyright (c) 2025, Extension and contributors
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
        {"label": "Contract Name", "fieldname": "name", "fieldtype": "Link", "options": "CRM Contract", "width": 160},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"label": "Region", "fieldname": "region", "fieldtype": "Data", "width": 120},
        {"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Region Branches", "width": 130},
        {"label": "Customer Name", "fieldname": "name", "fieldtype": "Link", "options": "CRM Organization", "width": 180},
        {"label": "Customer Address", "fieldname": "customer_address", "fieldtype": "Data", "width": 200},
        {"label": "Shipping Address", "fieldname": "shipping_address", "fieldtype": "Data", "width": 200},
        {"label": "Net Invoiced Amount", "fieldname": "total", "fieldtype": "Currency", "width": 140},
        {"label": "0–30 Days", "fieldname": "range1", "fieldtype": "Currency", "width": 100},
        {"label": "31–60 Days", "fieldname": "range2", "fieldtype": "Currency", "width": 100},
        {"label": "61–90 Days", "fieldname": "range3", "fieldtype": "Currency", "width": 100},
        {"label": "90+ Days", "fieldname": "range4", "fieldtype": "Currency", "width": 100},
    ]


def get_data(filters):
    today = nowdate()

    # 🧩 Build dynamic filter conditions safely
    conditions = ""
    if filters.get("branch"):
        conditions += " AND c.branch = %(branch)s"
    if filters.get("region"):
        conditions += " AND c.region = %(region)s"
    if filters.get("customer_name"):
        conditions += " AND c.customer_name = %(customer_name)s"
    if filters.get("project"):
        conditions += " AND c.project = %(project)s"
    if filters.get("customer_address"):
        conditions += " AND c.customer_address = %(customer_address)s"
    if filters.get("shipping_address"):
        conditions += " AND c.shipping_address = %(shipping_address)s"

    # 🧠 Fetch CRM Contract + Billing Schedule data
    contracts = frappe.db.sql(f"""
        SELECT 
            c.name AS name,
            c.amount AS contract_amt,
            ROUND(b.amount) AS amount,
            c.branch AS branch,
            c.region AS region,
            c.customer_name AS customer_name,
            c.customer_address AS customer_address,
            c.shipping_address AS shipping_address,
            c.project AS project,
            b.invoice_id AS invoice_id,
            b.Payment_date AS due_date
        FROM `tabCRM Contract` AS c
        LEFT JOIN `tabContract Billing Schedule` AS b 
            ON b.parent = c.name
        WHERE 
            b.amount > 0 
            AND c.docstatus = 1 
            AND b.invoice_id IS NOT NULL 
            AND b.payment_received_date IS NULL
            {conditions}
        ORDER BY c.name
    """, filters, as_dict=True)

    data = {}

    for con in contracts:
        # 🔹 Use due_date or fallback to today
        payment_ref_date = con.due_date or today
        age = date_diff(today, payment_ref_date)
        name = con.name or "Unassigned"

        # Initialize project-wise aggregation
        if name not in data:
            data[name] = {
                "name": name,
                "branch": con.branch,
                "region": con.region,
                "customer_name": con.customer_name,
                "customer_address": con.customer_address,
                "shipping_address": con.shipping_address,
                "project": con.project,
                "range1": 0,
                "range2": 0,
                "range3": 0,
                "range4": 0,
                "total": 0
            }

        # Categorize by ageing bucket
        if age <= 30:
            data[name]["range1"] += con.amount or 0
        elif age <= 60:
            data[name]["range2"] += con.amount or 0
        elif age <= 90:
            data[name]["range3"] += con.amount or 0
        else:
            data[name]["range4"] += con.amount or 0

        data[name]["total"] += con.amount or 0

    return list(data.values())
