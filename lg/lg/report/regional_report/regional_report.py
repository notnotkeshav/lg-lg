import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        # Label changed to Region
        {"label": _("Region"), "fieldname": "group_name", "fieldtype": "Data", "width": 180},
        {"label": _("No. of Live Contracts"), "fieldname": "renewable_count", "fieldtype": "Int", "width": 180},
        {"label": _("Live Contract Amount"), "fieldname": "renewable_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("No. of Expired Contracts"), "fieldname": "expired_count", "fieldtype": "Int", "width": 180},
        {"label": _("Expired Amount"), "fieldname": "expired_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("No. of War/Lost Conversion"), "fieldname": "war_lost_count", "fieldtype": "Int", "width": 200},
        {"label": _("War/Lost Amount"), "fieldname": "war_lost_amount", "fieldtype": "Currency", "width": 150},
    ]

def get_data(filters):
    conditions = ""
    
    if filters.get("region"): 
        conditions += f" AND region = {frappe.db.escape(filters.get('region'))}"
    
    if filters.get("asm"):
        full_name = frappe.db.get_value("User", filters.get("asm"), "full_name")
        conditions += f" AND asm_name = {frappe.db.escape(full_name)}"
    
    if filters.get("year"):
        conditions += f" AND YEAR(creation) = {frappe.db.escape(filters.get('year'))}"
        
    if filters.get("month"):
        months = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        if filters.get("month") in months:
            conditions += f" AND MONTH(creation) = {months.index(filters.get('month'))}"

    # Grouping logic changed from 'branch' to 'region'
    raw_data = frappe.db.sql(f"""
        SELECT 
            region as group_name,
            SUM(CASE WHEN custom_contract_status = 'Expired' THEN 1 ELSE 0 END) as expired_count,
            SUM(CASE WHEN custom_contract_status = 'Expired' THEN amount ELSE 0 END) as expired_amount,
            SUM(CASE WHEN deal_type = 'AMC Renewal' THEN 1 ELSE 0 END) as renewable_count,
            SUM(CASE WHEN deal_type = 'AMC Renewal' THEN amount ELSE 0 END) as renewable_amount,
            SUM(CASE WHEN deal_type IN ('Warranty AMC Conversion', 'Lost Warranty Conversion', 'Lost AMC Conversion') THEN 1 ELSE 0 END) as war_lost_count,
            SUM(CASE WHEN deal_type IN ('Warranty AMC Conversion', 'Lost Warranty Conversion', 'Lost AMC Conversion') THEN amount ELSE 0 END) as war_lost_amount
        FROM `tabCRM Contract`
        WHERE docstatus < 2 
        {conditions}
        GROUP BY region
    """, as_dict=1)

    return raw_data
