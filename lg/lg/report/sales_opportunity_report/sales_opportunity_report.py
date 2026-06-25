# Copyright (c) 2025, extension and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    filters = filters or {}

    conditions = []
    values = {}

    if filters.get("expiry_date"):
        conditions.append("p.expiry_date <= %(expiry_date)s")
        values["expiry_date"] = filters["expiry_date"]

    if filters.get("branch"):
        conditions.append("o.branch = %(branch)s")
        values["branch"] = filters["branch"]

    if filters.get("region"):
        conditions.append("o.region = %(region)s")
        values["region"] = filters["region"]

    condition_str = " AND ".join(conditions)
    if condition_str:
        condition_str = " AND " + condition_str

    query = f"""
        SELECT 
            o.name, o.region, o.branch, o.total_hp, o.project, o.register_date, o.commision_date,
            b.branch_head, r.region_head, o.warranty_expiry_date, p.expiry_date, p.current_deal,
            DATEDIFF(p.expiry_date, CURDATE()) AS days_to_expiry
        FROM `tabCRM Deal` AS o
        JOIN `tabRegion Branches` AS b ON b.name = o.branch
        JOIN `tabRegion Master` AS r ON r.name = o.region
        JOIN `tabProject` AS p ON p.name = o.project
        WHERE o.deal_category = "Sales"
        {condition_str}
    """

    data = frappe.db.sql(query, values, as_dict=True)

    columns = [
        {"label": "Deal", "fieldname": "name", "fieldtype": "Link", "options": "CRM Deal", "width": 150},
        {"label": "Region", "fieldname": "region", "fieldtype": "Link", "options": "Region Master", "width": 120},
        {"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Region Branches", "width": 120},
        {"label": "Total HP", "fieldname": "total_hp", "fieldtype": "Float", "width": 100},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"label": "Register Date", "fieldname": "register_date", "fieldtype": "Date", "width": 120},
        {"label": "Commission Date", "fieldname": "commision_date", "fieldtype": "Date", "width": 120},
        {"label": "Branch Head", "fieldname": "branch_head", "fieldtype": "Data", "width": 120},
        {"label": "Region Head", "fieldname": "region_head", "fieldtype": "Data", "width": 120},
        {"label": "Warranty Expiry", "fieldname": "warranty_expiry_date", "fieldtype": "Date", "width": 120},
        {"label": "Project Expiry", "fieldname": "expiry_date", "fieldtype": "Date", "width": 120},
        {"label": "Current Deal", "fieldname": "current_deal", "fieldtype": "Data", "width": 120},
        {"label": "Days to Expiry", "fieldname": "days_to_expiry", "fieldtype": "Int", "width": 120},
    ]

    return columns, data
