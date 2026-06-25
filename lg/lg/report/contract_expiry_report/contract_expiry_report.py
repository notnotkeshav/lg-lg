from __future__ import unicode_literals
import frappe
import json
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

@frappe.whitelist()
def execute(filters=None):
    columns = get_columns()
    data = []

    if isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except Exception as e:
            frappe.log_error(f"❌ Filter Parse Error: {e}", str(filters))
            return columns, data

    
    if not filters:
        filters = {"period_type": "Days", "days_value": 30}

    

    today = date.today()

    
    if filters.get("period_type") == "Days":
        end_date = today + timedelta(days=int(filters.get("days_value", 0)))
    elif filters.get("period_type") == "Months":
        end_date = today + relativedelta(months=int(filters.get("months_value", 0)))
    else:
        end_date = today

    
    data = frappe.db.sql("""
        SELECT 
            name AS contract,
            project,
            from_deal AS Opportunity,
            customer,
            expiry_date,
            total_hp AS total_hp,
            price_rate,
            amount
        FROM `tabCRM Contract`
        WHERE expiry_date > %s AND expiry_date <= %s
        ORDER BY expiry_date
    """, (today, end_date), as_dict=True)

    return columns, data

def get_columns():
    return [
        {"label": "Contract", "fieldname": "contract", "fieldtype": "Link", "options": "CRM Contract", "width": 200},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 200},
        {"label": "Opportunity", "fieldname": "Opportunity", "fieldtype": "Link", "options": "CRM Deal", "width": 200},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "CRM Organization", "width": 200},
        {"label": "Expiry Date", "fieldname": "expiry_date", "fieldtype": "Date", "width": 120},
        {"label": "Total HP", "fieldname": "total_hp", "fieldtype": "Float", "width": 100},
        {"label": "Price Rate", "fieldname": "price_rate", "fieldtype": "Float", "width": 100},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Float", "width": 100}
    ]


# @frappe.whitelist()
# def execute(filters=None):
#     columns = get_columns()
#     data = []

#     if not filters:
#         return columns, data

#     today = date.today()

  
#     if filters.get("period_type") == "Days":
#         end_date = today + timedelta(days=int(filters.get("days_value", 0)))
#     elif filters.get("period_type") == "Months":
#         end_date = today + relativedelta(months=int(filters.get("months_value", 0)))
#     else:
#         end_date = today

#     # Fetch data
#     data = frappe.db.sql("""
#         SELECT 
#             name AS Contract,
#             expiry_date AS `Expiry Date`,
#             hp AS `Total HP`,
#             price_rate AS `Price Rate`
                         
                         
#         FROM 
#             `tabCRM Contract`
#         WHERE 
#             expiry_date > %s AND expiry_date <= %s
#         ORDER BY expiry_date
#     """, (today, end_date), as_dict=True)

#     return columns, data

# def get_columns():
#     return [
#         {"label": "Contract", "fieldname": "Contract", "fieldtype": "Link", "options": "CRM Contract", "width": 200},
#         {"label": "Expiry Date", "fieldname": "Expiry Date", "fieldtype": "Date", "width": 120},
#         {"label": "Total HP", "fieldname": "Total HP", "fieldtype": "Float", "width": 100},
#         {"label": "Price Rate", "fieldname": "Price Rate", "fieldtype": "Float", "width": 100}
#     ]
