import frappe

def execute(filters=None):
    filters = filters or {}
    to_date = filters.get("to_date")

    if not to_date:
        frappe.throw("Please select a 'To Date' to see overdue billing items.")

    conditions = ["b.billing_date <= %(to_date)s"]
    sql_filters = {"to_date": to_date}

    if filters.get("customer"):
        conditions.append("c.customer = %(customer)s")
        sql_filters["customer"] = filters["customer"]

    if filters.get("project"):
        conditions.append("c.project = %(project)s")
        sql_filters["project"] = filters["project"]

    conditions.append("(b.status IS NULL OR b.status != 'Paid')")

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT 
            c.name AS contract_id,
            c.customer,
            c.project,
            b.billing_date,
            b.amount,
            b.status,
            DATEDIFF(%(to_date)s, b.billing_date) AS days_overdue
        FROM 
            `tabContract Billing Schedule` AS b
        JOIN 
            `tabCRM Contract` AS c ON c.name = b.parent
        WHERE 
            {where_clause}
        ORDER BY 
            b.billing_date ASC
    """

    data = frappe.db.sql(query, sql_filters, as_dict=1)

    columns = [
        {"label": "Contract ID", "fieldname": "contract_id", "fieldtype": "Link", "options": "CRM Contract", "width": 150},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "CRM Organization", "width": 150},
        {"label": "Project", "fieldname": "project", "fieldtype": "Data", "width": 150},
        {"label": "Billing Date", "fieldname": "billing_date", "fieldtype": "Date", "width": 120},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Days Overdue", "fieldname": "days_overdue", "fieldtype": "Int", "width": 100},
    ]

    return columns, data
