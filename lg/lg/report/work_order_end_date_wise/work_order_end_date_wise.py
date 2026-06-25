import frappe

def execute(filters=None):
    columns = [
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
        {"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
        {"label": "Zone", "fieldname": "region", "fieldtype": "Data", "width": 120},
        {"label": "Start Date", "fieldname": "start_date", "fieldtype": "Date", "width": 110},
        {"label": "Expiry Date", "fieldname": "expiry_date", "fieldtype": "Date", "width": 110},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "Dealer Name", "fieldname": "ssd_name_dealer", "fieldtype": "Data", "width": 160},
        {"label": "Bill To Code", "fieldname": "bill_ship_code", "fieldtype": "Data", "width": 130},
        {"label": "Customer PO ID", "fieldname": "customer_po_id", "fieldtype": "Data", "width": 130},
        {"label": "Customer PO Date", "fieldname": "customer_po_date", "fieldtype": "Date", "width": 120},
        {"label": "Work Order Issue Date", "fieldname": "work_order_issue_date", "fieldtype": "Date", "width": 150},
    ]

    conditions = []
    values = {}

    if filters.get("customer_name"):
        conditions.append("customer_name = %(customer_name)s")
        values["customer_name"] = filters["customer_name"]

    if filters.get("branch"):
        conditions.append("branch = %(branch)s")
        values["branch"] = filters["branch"]

    if filters.get("region"):
        conditions.append("region = %(region)s")
        values["region"] = filters["region"]

    if filters.get("ssd_name_dealer"):
        conditions.append("ssd_name_dealer LIKE %(ssd_name_dealer)s")
        values["ssd_name_dealer"] = f"%{filters['ssd_name_dealer']}%"

    if filters.get("bill_ship_code"):
        conditions.append("bill_ship_code = %(bill_ship_code)s")
        values["bill_ship_code"] = filters["bill_ship_code"]

    if filters.get("from_start_date"):
        conditions.append("start_date >= %(from_start_date)s")
        values["from_start_date"] = filters["from_start_date"]

    if filters.get("to_start_date"):
        conditions.append("start_date <= %(to_start_date)s")
        values["to_start_date"] = filters["to_start_date"]

    if filters.get("from_expiry_date"):
        conditions.append("expiry_date >= %(from_expiry_date)s")
        values["from_expiry_date"] = filters["from_expiry_date"]

    if filters.get("to_expiry_date"):
        conditions.append("expiry_date <= %(to_expiry_date)s")
        values["to_expiry_date"] = filters["to_expiry_date"]

    condition_str = " AND ".join(conditions)
    if condition_str:
        condition_str = "WHERE " + condition_str

    data = frappe.db.sql(
        f"""
        SELECT
            customer_name,
            branch,
            region,
            start_date,
            expiry_date,
            amount,
            ssd_name_dealer,
            bill_ship_code,
            customer_po_id,
            customer_po_date,
            work_order_issue_date
        FROM `tabCRM Contract`
        {condition_str}
        ORDER BY start_date DESC
        """,
        values,
        as_dict=True
    )

    return columns, data
