# Copyright (c) 2024, extension and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data
import frappe

def execute(filters=None):
    # Initialize filters if not provided
    if not filters:
        filters = {}

    # Fetch data based on filters
    data = get_data(filters)
    
    # Generate columns dynamically based on data
    columns = get_columns(data)
    
    return columns, data


def get_columns(data):
    columns = [
        {"label": "Customer Name", "fieldname": "customer", "fieldtype": "Data"},
        {"label": "Customer HC", "fieldname": "customer_hc", "fieldtype": "Data"},
        {"label": "Contract ID", "fieldname": "name", "fieldtype": "Link", "options": "CRM Contract"},
        {"label": "Contract From", "fieldname": "contract_from", "fieldtype": "Data"},
        {"label": "AMC", "fieldname": "amc", "fieldtype": "Data"},
        {"label": "Start Date", "fieldname": "start_date", "fieldtype": "Date"},
        {"label": "Expiry Date", "fieldname": "expiry_date", "fieldtype": "Date"},
        {"label": "Total Amount", "fieldname": "amount", "fieldtype": "Float"},
        {"label": "Payment Frequency", "fieldname": "payment_frequency", "fieldtype": "Data"},
    ]

    # Dynamically adjust column widths if data is available
    if data:
        for column in columns:
            label_length = len(column["label"])
            fieldname = column["fieldname"]
            
            # Calculate max data length for the column
            max_data_length = max(len(str(row.get(fieldname, ""))) for row in data)
            
            # Set width based on the larger of label or max data length
            column["width"] = max(label_length, max_data_length) * 10 + 20

    return columns


def get_conditions(filters):
    conditions = []
    values = filters or {}

    if filters.get("start_date"):
        conditions.append("start_date >= %(start_date)s")
    # if filters.get("end_date"):
    #     conditions.append("expiry_date <= %(end_date)s")
    if 'customer' in filters:
        conditions.append("customer = %(customer)s")
    # if 'contract_from' in filters:
    #     conditions.append("contract_from = %(contract_from)s")
    if 'payment_frequency' in filters:
        conditions.append("payment_frequency = %(payment_frequency)s")
    
    return " AND ".join(conditions) if conditions else "", values


def get_data(filters):
    conditions, values = get_conditions(filters)
    conditions = f"WHERE {conditions}" if conditions else ""

    query = f"""
        SELECT 
            customer,
            customer_hc,
            name,
            CASE 
                WHEN contract_from = 'CRM Deal' THEN from_deal 
                ELSE from_quote 
            END AS contract_from,
            amc,
            start_date,
            expiry_date,
            amount,
            payment_frequency
        FROM 
            `tabCRM Contract`
        {conditions}
    """

    data = frappe.db.sql(query, values, as_dict=True)

    # # Calculate totals
    # total_amount = sum(row['amount'] for row in data)

    # # Append a total row
    # total_row = {
    #     'customer': 'Total',
    #     'customer_hc': '',
    #     'name': '',
    #     'contract_from': '',
    #     'amc': '',
    #     'start_date': '',
    #     'expiry_date': '',
    #     'amount': total_amount,
    #     'payment_frequency': '',
    # }
    
    # data.append(total_row)
    
    return data
