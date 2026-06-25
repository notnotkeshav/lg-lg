# Copyright (c) 2025, extension and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    filters = filters or {}
    values = {}

    if not filters.get("year"):
        filters["year"] = frappe.utils.now_datetime().year  # default current year

    values["year"] = filters["year"]

    conditions = []
    if filters.get("region"):
        conditions.append("o.region = %(region)s")
        values["region"] = filters["region"]

    if filters.get("branch"):
        conditions.append("o.branch = %(branch)s")
        values["branch"] = filters["branch"]

    condition_str = " AND ".join(conditions)
    if condition_str:
        condition_str = " AND " + condition_str

    query = f"""
        SELECT 
            o.region,
            r.region_head_name AS region_head,
            o.branch,
            b.branch_head_name AS branch_head,
            o.deal_category,
            COUNT(DISTINCT o.name) AS opportunity_count,
            SUM(pd.hp) AS total_hp,

            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 1 THEN 1 ELSE 0 END) AS Jan,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 2 THEN 1 ELSE 0 END) AS Feb,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 3 THEN 1 ELSE 0 END) AS Mar,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 4 THEN 1 ELSE 0 END) AS Apr,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 5 THEN 1 ELSE 0 END) AS May,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 6 THEN 1 ELSE 0 END) AS Jun,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 7 THEN 1 ELSE 0 END) AS Jul,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 8 THEN 1 ELSE 0 END) AS Aug,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 9 THEN 1 ELSE 0 END) AS Sep,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 10 THEN 1 ELSE 0 END) AS Oct,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 11 THEN 1 ELSE 0 END) AS Nov,
            SUM(CASE WHEN MONTH(o.warranty_expiry_date) = 12 THEN 1 ELSE 0 END) AS `Dec`
        FROM `tabCRM Deal` AS o
        JOIN `tabProduct Details` AS pd ON pd.parent = o.name
        JOIN `tabRegion Master` AS r ON r.name=o.region
        JOIN `tabRegion Branches` AS b on b.name=o.branch
        WHERE o.deal_category = "Sales"
          AND YEAR(o.warranty_expiry_date) = %(year)s
          {condition_str}
        GROUP BY o.region, o.branch, o.deal_category
        ORDER BY o.region, o.branch
    """

    data = frappe.db.sql(query, values, as_dict=True)

    columns = [
        {"label": "Region", "fieldname": "region", "fieldtype": "Link", "options": "Region Master", "width": 120},
		{"label": "Region Head", "fieldname": "region_head", "fieldtype": "Data", "width": 120},
        {"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Region Branches", "width": 120},
		{"label": "Branch Head", "fieldname": "branch_head", "fieldtype": "Data", "width": 120},
        {"label": "Opportunities Count", "fieldname": "opportunity_count", "fieldtype": "Int", "width": 200},
        {"label": "Total HP", "fieldname": "total_hp", "fieldtype": "Int", "width": 120},
    ]

    # Add months dynamically
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for m in months:
        columns.append({"label": m, "fieldname": m, "fieldtype": "Int", "width": 80})

    return columns, data
