import json
import frappe

@frappe.whitelist()
def execute(filters=None):
    # ✅ Handle string filters from frontend/API call
    if isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except Exception as e:
            frappe.log_error(f"Error parsing filters: {e}", filters)
            filters = {}

    filters = filters or {}

    conditions = []
    if filters.get("customer"):
        conditions.append("c.name = %(customer)s")
    if filters.get("project"):
        conditions.append("pi.project_name = %(project)s")
    if filters.get("status"):
        conditions.append("pi.status = %(status)s")
    if filters.get("vertical"):
        conditions.append("c.industry = %(vertical)s")
    if filters.get("region"):
        conditions.append("c.region = %(region)s")

    condition_sql = "WHERE " + " AND ".join(conditions) if conditions else ""

    data = frappe.db.sql(
        f"""
        SELECT
            pi.project_name AS "Project",
            c.name AS "Customer",
            c.organization_name AS "Customer Name",
            c.region AS `Region`,
            c.industry AS `Vertical`,
            pi.status AS "Status",
            pi.expiry_date AS "Expiry Date",
            pi.customer_address AS "Bill To",
            pi.shipping_address AS "Ship To"
        FROM
            `tabCRM Organization` c
        JOIN
            `tabProject` pi ON pi.customer = c.name
        {condition_sql}
        ORDER BY
            pi.expiry_date
        """,
        filters,
        as_dict=True
    )

    columns = [
        {"label": "<b>Customer</b>", "fieldname": "Customer", "fieldtype": "Link", "options": "CRM Organization", "width": 180},
        {"label": "<b>Customer Name</b>", "fieldname": "Customer Name", "fieldtype": "Data", "width": 180},
        {"label": "<b>Project</b>", "fieldname": "Project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"label": "<b>Expiry Date</b>", "fieldname": "Expiry Date", "fieldtype": "Date", "width": 120},
        {"label": "<b>Vertical</b>", "fieldname": "Vertical", "fieldtype": "Link", "options": "CRM Industry", "width": 150},
        {"label": "<b>Region</b>", "fieldname": "Region", "fieldtype": "Link", "options": "Region Master", "width": 120},
        {"label": "<b>Status</b>", "fieldname": "Status", "fieldtype": "Select", "width": 120},
        {"label": "<b>Bill To</b>", "fieldname": "Bill To", "fieldtype": "Link", "options": "Address", "width": 120},
        {"label": "<b>Ship To</b>", "fieldname": "Ship To", "fieldtype": "Link", "options": "Address", "width": 120},
    ]

    return columns, data




# # Copyright (c) 2025, extension and contributors
# # For license information, please see license.txt

# import frappe


# # your_app/your_app/report/project_summary_report/project_summary_report.py

# import frappe

# @frappe.whitelist()
# def execute(filters=None):
#     filters = filters or {}
    
#     conditions = []
#     if filters.get("customer"):
#         conditions.append("c.name = %(customer)s")
#     if filters.get("project"):
#         conditions.append("pi.project_name = %(project)s")
#     if filters.get("status"):
#         conditions.append("pi.status = %(status)s")
#     if filters.get("vertical"):
#         conditions.append("c.industry = %(vertical)s")
#     if filters.get("region"):
#         conditions.append("c.region = %(region)s")

#     condition_sql = "WHERE " + " AND ".join(conditions) if conditions else ""

#     data = frappe.db.sql(
#         f"""
#         SELECT
#             pi.project_name AS "Project",
#             c.name AS "Customer",
#             c.organization_name AS "Customer Name",
#             c.region AS `Region`,
#             c.industry AS `Vertical`,
#             pi.status AS "Status",
#             pi.expiry_date AS "Expiry Date",
#             pi.customer_address AS "Bill To",
#             pi.shipping_address AS "Ship To"
#         FROM
#             `tabCRM Organization` c
#         JOIN
#             `tabProject` pi ON pi.customer = c.name
        
#         {condition_sql}

#         ORDER BY
#             pi.expiry_date
#         """,
#         filters,
#         as_dict=True
#     )

#     columns = [
#         {"label": "<b>Customer</b>", "fieldname": "Customer", "fieldtype": "Link", "options": "CRM Organization", "width": 180},
#         {"label": "<b>Customer Name</b>", "fieldname": "Customer Name", "fieldtype": "Data", "width": 180},
#         {"label": "<b>Project</b>", "fieldname": "Project", "fieldtype": "Link", "options": "Project", "width": 150},
#         {"label": "<b>Expiry Date</b>", "fieldname": "Expiry Date", "fieldtype": "Date", "width": 120},
#         {"label": "<b>Vertical</b>", "fieldname": "Vertical", "fieldtype": "Link","options":"CRM Industry", "width": 150},
#         {"label": "<b>Region</b>", "fieldname": "Region", "fieldtype": "Link","options":"Region Master", "width": 120},
#         {"label": "<b>Status</b>", "fieldname": "Status", "fieldtype": "Select", "width": 120},
#         {"label": "<b>Bill To</b>", "fieldname": "Bill To", "fieldtype": "Link","options":"Address", "width": 120},
#         {"label": "<b>Ship To</b>", "fieldname": "Ship To", "fieldtype": "Link","options":"Address", "width": 120},
#     ]

#     return columns, data
