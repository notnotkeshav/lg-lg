# import frappe
# from frappe import _

# def execute(filters=None):
#     columns = get_columns()
#     data = get_data(filters)
#     return columns, data

# def get_columns():
#     return [
#         {"label": _("Branch"), "fieldname": "group_name", "fieldtype": "Data", "width": 150},
#         {"label": _("No. of Live Contracts"), "fieldname": "renewable_count", "fieldtype": "Int", "width": 180},
#         {"label": _("Live Contract Amount"), "fieldname": "renewable_amount", "fieldtype": "Currency", "width": 150}
#         {"label": _("No. of Expired Contracts"), "fieldname": "expired_count", "fieldtype": "Int", "width": 180},
#         {"label": _("Expired Amount"), "fieldname": "expired_amount", "fieldtype": "Currency", "width": 150},
        
#     ]

# def get_data(filters):
#     conditions = ""
#     # Filter by Region, Branch, ASM
#     if filters.get("region"): conditions += f" AND region = '{filters.get('region')}'"
#     if filters.get("branch"): conditions += f" AND branch = '{filters.get('branch')}'"
#     if filters.get("asm"):
#         # Convert User ID to Full Name to match the 'asm_name' field in Contract
#         full_name = frappe.db.get_value("User", filters.get("asm"), "full_name")
#         conditions += f" AND asm_name = {frappe.db.escape(full_name)}"
    
#     # Filter by Month/Year (assuming 'start_date' or 'posting_date' is the reference)
#     if filters.get("year"):
#         conditions += f" AND YEAR(creation) = '{filters.get('year')}'"
#     if filters.get("month"):
#         month_index = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].index(filters.get("month"))
#         conditions += f" AND MONTH(creation) = {month_index}"

#     # Query logic: 
#     # Expired = custom_contract_status == 'Expired'
#     # Renewable = deal_type == 'Renewable'
#     # Others are excluded automatically by these conditions
#     raw_data = frappe.db.sql(f"""
#         SELECT 
#             branch as group_name,
#             SUM(CASE WHEN custom_contract_status = 'Expired' THEN 1 ELSE 0 END) as expired_count,
#             SUM(CASE WHEN custom_contract_status = 'Expired' THEN amount ELSE 0 END) as expired_amount,
#             SUM(CASE WHEN deal_type = 'AMC Renewal' THEN 1 ELSE 0 END) as renewable_count,
#             SUM(CASE WHEN deal_type = 'AMC Renewal' THEN amount ELSE 0 END) as renewable_amount
#         FROM `tabCRM Contract`
#         WHERE docstatus < 2 
#         {conditions}
#         GROUP BY branch
#     """, as_dict=1)

#     return raw_data


import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Branch"), "fieldname": "group_name", "fieldtype": "Data", "width": 150},
        {"label": _("No. of Live Contracts"), "fieldname": "renewable_count", "fieldtype": "Int", "width": 180},
        {"label": _("Live Contract Amount"), "fieldname": "renewable_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("No. of Expired Contracts"), "fieldname": "expired_count", "fieldtype": "Int", "width": 180},
        {"label": _("Expired Amount"), "fieldname": "expired_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("No. of War/Lost Conversion"), "fieldname": "war_lost_count", "fieldtype": "Int", "width": 200},
        {"label": _("War/Lost Amount"), "fieldname": "war_lost_amount", "fieldtype": "Currency", "width": 150},
        
    ]

def get_data(filters):
    conditions = ""
    # Filter by Region, Branch, ASM
    if filters.get("region"): conditions += f" AND region = '{filters.get('region')}'"
    if filters.get("branch"): conditions += f" AND branch = '{filters.get('branch')}'"
    if filters.get("asm"):
        full_name = frappe.db.get_value("User", filters.get("asm"), "full_name")
        conditions += f" AND asm_name = {frappe.db.escape(full_name)}"
    
    # Filter by Month/Year
    if filters.get("year"):
        conditions += f" AND YEAR(creation) = '{filters.get('year')}'"
    if filters.get("month"):
        month_index = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].index(filters.get("month"))
        conditions += f" AND MONTH(creation) = {month_index}"

    # Query logic updated for War/Lost Conversion
    raw_data = frappe.db.sql(f"""
        SELECT 
            branch as group_name,
            SUM(CASE WHEN custom_contract_status = 'Expired' THEN 1 ELSE 0 END) as expired_count,
            SUM(CASE WHEN custom_contract_status = 'Expired' THEN amount ELSE 0 END) as expired_amount,
            SUM(CASE WHEN deal_type = 'AMC Renewal' THEN 1 ELSE 0 END) as renewable_count,
            SUM(CASE WHEN deal_type = 'AMC Renewal' THEN amount ELSE 0 END) as renewable_amount,
            SUM(CASE WHEN deal_type IN ('Warranty AMC Conversion', 'Lost Warranty Conversion', 'Lost AMC Conversion') THEN 1 ELSE 0 END) as war_lost_count,
            SUM(CASE WHEN deal_type IN ('Warranty AMC Conversion', 'Lost Warranty Conversion', 'Lost AMC Conversion') THEN amount ELSE 0 END) as war_lost_amount
        FROM `tabCRM Contract`
        WHERE docstatus < 2 
        {conditions}
        GROUP BY branch
    """, as_dict=1)

    return raw_data
