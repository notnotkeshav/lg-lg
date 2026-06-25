# warranty_management/api/dashboard.py

import frappe
from frappe import _

@frappe.whitelist()
def get_warranty_stats(date_range=None, product=None, status=None):
    filters = build_filters(date_range, product, status)
    
    total_warranties = frappe.get_all(
        "Warranty",
        filters=filters,
        count=True
    )
    
    active_warranties = frappe.get_all(
        "Warranty",
        filters={**filters, "status": "Active"},
        count=True
    )
    
    expiring_soon = frappe.get_all(
        "Warranty",
        filters={**filters, "status": "Expiring Soon"},
        count=True
    )
    
    return {
        "total_warranties": total_warranties,
        "active_warranties": active_warranties,
        "expiring_soon": expiring_soon,
        "total_change": calculate_change("total", date_range),
        "active_change": calculate_change("active", date_range),
        "expiring_change": calculate_change("expiring", date_range)
    }

@frappe.whitelist()
def get_warranty_by_status(date_range=None, product=None, status=None):
    filters = build_filters(date_range, product, status)
    
    data = frappe.get_all(
        "Warranty",
        filters=filters,
        fields=["status", "count(name) as count"],
        group_by="status"
    )
    
    return data

@frappe.whitelist()
def get_warranty_by_product(date_range=None, product=None, status=None):
    filters = build_filters(date_range, product, status)
    
    data = frappe.get_all(
        "Warranty",
        filters=filters,
        fields=["product", "count(name) as count"],
        group_by="product"
    )
    
    return data

@frappe.whitelist()
def get_recent_warranties(date_range=None, product=None, status=None):
    filters = build_filters(date_range, product, status)
    
    warranties = frappe.get_all(
        "Warranty",
        filters=filters,
        fields=["name", "customer", "product", "status", "start_date", "end_date"],
        order_by="creation desc",
        limit=10
    )
    
    return warranties

@frappe.whitelist()
def get_funnel_data():
    try:
        # Get all valid deal statuses
        deal_statuses = frappe.get_all("CRM Deal Status", pluck="name")
        
        # Create a dictionary to store counts for each status
        stages = {}
        for status in deal_statuses:
            count = frappe.db.count("CRM Deal", {"status": status})
            stages[status] = count
        
        # Sort stages by count in descending order to create funnel effect
        sorted_stages = dict(sorted(stages.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "status": "success",
            "data": sorted_stages
        }
    except Exception as e:
        frappe.log_error(f"Error in get_funnel_data: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

def build_filters(date_range, product, status):
    filters = {}
    
    if date_range:
        # Add date range filter logic
        pass
        
    if product:
        filters["product"] = product
        
    if status:
        filters["status"] = status
        
    return filters