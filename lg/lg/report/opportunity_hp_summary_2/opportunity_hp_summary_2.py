import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    group_by = filters.get("group_by") or "Project"
    chart_type = filters.get("chart_type") or "bar"
    date_range_type = filters.get("date_range_type") or "Previous 6 Months"

    where_clauses = ["cd.docstatus < 2"]
    params = {}

    # --- Date range logic ---
    from_date, to_date = get_date_range(filters)
    where_clauses.append("cd.register_date BETWEEN %(from_date)s AND %(to_date)s")
    params["from_date"], params["to_date"] = from_date, to_date

    # --- Additional filters ---
    if filters.get("project"):
        where_clauses.append("cd.project = %(project)s")
        params["project"] = filters.get("project")
    if filters.get("branch"):
        where_clauses.append("cd.branch = %(branch)s")
        params["branch"] = filters.get("branch")
    if filters.get("region"):
        where_clauses.append("cd.region = %(region)s")
        params["region"] = filters.get("region")

    where_sql = " AND ".join(where_clauses)

    # --- Group By Mapping ---
    group_field_map = {
        "Project": "cd.project",
        "Branch": "cd.branch",
        "Region": "cd.region",
        "AM": "COALESCE(rb.branch_head_name, cd.owner)",
        "RSM": "rm.region_head_name"
    }
    group_field = group_field_map.get(group_by, "cd.project")

    # --- If chart type is line: change logic ---
    if chart_type == "line":
        time_group_field = get_time_group_field(date_range_type)
        query = f"""
            SELECT
                {group_field} AS group_label,
                {time_group_field} AS period_label,
                SUM(COALESCE(pd.hp, 0)) AS total_hp
            FROM `tabCRM Deal` cd
            LEFT JOIN `tabProduct Details` pd ON pd.parent = cd.name
            LEFT JOIN `tabRegion Branches` rb ON rb.name = cd.branch
            LEFT JOIN `tabRegion Master` rm ON rm.name = cd.region
            WHERE {where_sql}
            GROUP BY group_label, period_label
            ORDER BY MIN(cd.register_date)
        """
        results = frappe.db.sql(query, params, as_dict=True)

        # Prepare data for line chart
        grouped = {}
        for r in results:
            grouped.setdefault(r.group_label or "Undefined", {})[r.period_label] = r.total_hp

        all_periods = sorted({r["period_label"] for r in results})
        chart = {
            "data": {
                "labels": all_periods,
                "datasets": [
                    {"name": g, "values": [grouped[g].get(p, 0) for p in all_periods]}
                    for g in grouped
                ]
            },
            "type": "line"
        }

        # Table columns
        columns = [
            {"fieldname": "group_label", "label": _(group_by), "fieldtype": "Data", "width": 250},
            {"fieldname": "period_label", "label": _("Period"), "fieldtype": "Data", "width": 150},
            {"fieldname": "total_hp", "label": _("Total HP"), "fieldtype": "Float", "width": 120}
        ]

        data = results
        report_summary = [{"label": _("Total HP (All)"), "value": sum(r.total_hp for r in results)}]

        return columns, data, None, chart, report_summary

    # --- Default (all other charts as-is) ---
    query = f"""
        SELECT
            {group_field} AS group_label,
            SUM(COALESCE(pd.hp, 0)) AS total_hp,
            COUNT(pd.name) AS product_count
        FROM `tabCRM Deal` cd
        LEFT JOIN `tabProduct Details` pd ON pd.parent = cd.name
        LEFT JOIN `tabRegion Branches` rb ON rb.name = cd.branch
        LEFT JOIN `tabRegion Master` rm ON rm.name = cd.region
        WHERE {where_sql}
        GROUP BY {group_field}
        ORDER BY total_hp DESC
    """
    results = frappe.db.sql(query, params, as_dict=True)

    # Columns
    columns = [
        {"fieldname": "group_label", "label": _(group_by), "fieldtype": "Data", "width": 300},
        {"fieldname": "total_hp", "label": _("Total HP"), "fieldtype": "Float", "width": 140},
        {"fieldname": "product_count", "label": _("Product Rows"), "fieldtype": "Int", "width": 120}
    ]

    data = []
    grand_total_hp = 0
    for row in results:
        grand_total_hp += row.total_hp or 0
        data.append(row)

    chart = {
        "data": {
            "labels": [d["group_label"] for d in data],
            "datasets": [{"name": _("Total HP"), "values": [d["total_hp"] for d in data]}]
        },
        "type": chart_type
    }

    report_summary = [
        {"value": f"{grand_total_hp:,.0f}", "indicator": "Green" if grand_total_hp > 0 else "Red",
         "label": _("Total HP (All)"), "datatype": "Data"},
        {"value": sum(d["product_count"] for d in data), "label": _("Total Product Rows"), "datatype": "Int"}
    ]

    return columns, data, None, chart, report_summary


# --- Helper: Get date range ---
def get_date_range(filters):
    import datetime
    from frappe.utils import getdate, add_months, nowdate

    today = getdate(nowdate())
    dr = filters.get("date_range_type")

    if dr == "Current Month":
        from_date = today.replace(day=1)
        to_date = today
    elif dr == "Previous Month":
        from_date = add_months(today.replace(day=1), -1)
        to_date = from_date.replace(day=28)  # approx end
    elif dr == "Previous 3 Months":
        from_date = add_months(today, -3)
        to_date = today
    elif dr == "Previous 6 Months":
        from_date = add_months(today, -6)
        to_date = today
    elif dr == "Current Quarter":
        q = (today.month - 1) // 3 + 1
        from_date = datetime.date(today.year, 3 * q - 2, 1)
        to_date = today
    elif dr == "Current Year":
        from_date = datetime.date(today.year, 1, 1)
        to_date = today
    elif dr == "Previous Year":
        from_date = datetime.date(today.year - 1, 1, 1)
        to_date = datetime.date(today.year - 1, 12, 31)
    elif filters.get("from_date") and filters.get("to_date"):
        from_date, to_date = filters["from_date"], filters["to_date"]
    else:
        from_date = add_months(today, -6)
        to_date = today

    return from_date, to_date


# --- Helper: Time grouping ---
def get_time_group_field(date_range_type):
    if "Month" in date_range_type:
        # For current month → show day labels (e.g. 01-Oct)
        return "DATE_FORMAT(cd.register_date, '%%d-%%b')"
    elif "Quarter" in date_range_type:
        # For quarter → show Q1, Q2, etc.
        return "CONCAT('Q', QUARTER(cd.register_date))"
    else:
        # For year or multi-month → show month labels (e.g. Jan, Feb)
        return "DATE_FORMAT(cd.register_date, '%%b')"

