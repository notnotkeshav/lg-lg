import frappe
import json

@frappe.whitelist(allow_guest=True)
def test_post_api():
    """Simple POST API to echo back received data"""
    try:
        if frappe.request.method != "POST":
            frappe.throw("Only POST requests are allowed")

        data = json.loads(frappe.request.data)
        return {"status": "success", "received": data}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Test API Error")
        frappe.response.http_status_code = 400
        return {"status": "error", "message": str(e)}