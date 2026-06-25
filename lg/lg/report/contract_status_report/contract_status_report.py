import frappe

def execute(filters=None):
    if not filters: filters = {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Region", "fieldname": "region", "fieldtype": "Link", "options": "Region Master", "width": 160},
        {"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Region Branches", "width": 160},
        {"label": "ASM Name", "fieldname": "asm_name", "fieldtype": "Data", "width": 160},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
        {"label": "Expiry Date", "fieldname": "expiry_date", "fieldtype": "Date", "width": 120},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
		{"label": "Contract type", "fieldname": "deal_type", "fieldtype": "data", "width": 250},
    ]

def get_data(filters):
    # Base condition: Filter se status uthayega, agar nahi mila toh default 'Expired'
    status_filter = filters.get("status") or "Expired"
    conditions = " WHERE custom_contract_status = %(status)s"

    if filters.get("region"):
        conditions += " AND region = %(region)s"

    if filters.get("branch"):
        conditions += " AND branch = %(branch)s"

    if filters.get("asm_name"):
        conditions += " AND asm_name = %(asm_name)s"

    query = f"""
        SELECT
            region,
            branch,
            asm_name,
            customer_name,
            expiry_date,
			amount,
			deal_type
        FROM
            `tabCRM Contract`
        {conditions}
        ORDER BY expiry_date DESC
    """
    
    # filters dict ko pass kar rahe hain taaki %(status)s map ho sake
    return frappe.db.sql(query, filters, as_dict=True)
