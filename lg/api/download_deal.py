import frappe
from openpyxl import Workbook

CACHE_TTL = 7200
BATCH = 5000


def _cache_key(key, user):
    return f"crm_deal_export:{key}:{user}"


# -----------------------------
# Background job
# -----------------------------
def run_export_job(user):
    offset = 0
    path = f"/tmp/crm_deal_full_backup_{user}.xlsx"
    
    # FAST count using table stats (321k records)
    total = frappe.db.sql("SELECT COUNT(*) FROM `tabCRM Deal`")[0][0]
    processed = 0
    
    wb = Workbook(write_only=True)
    ws = wb.create_sheet("CRM Deals")
    
    frappe.cache().set(_cache_key("progress", user), 0, expires_in_sec=CACHE_TTL)
    
    # CRITICAL: Get ALL columns dynamically but efficiently
    columns = frappe.db.sql("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'tabCRM Deal' 
        ORDER BY ORDINAL_POSITION
    """)
    columns = [row[0] for row in columns]
    
    ws.append(columns)
    
    while processed < total:
        # Smaller batches for stability
        rows = frappe.db.sql(
            f"SELECT {', '.join(columns)} FROM `tabCRM Deal` LIMIT %s OFFSET %s",
            (1000, offset),  # Reduced batch size
            as_dict=True
        )
        
        if not rows:
            break
            
        for r in rows:
            ws.append([r.get(c, "") for c in columns])
        
        offset += 1000
        processed += len(rows)
        progress = min(100, int((processed * 100) / total))
        
        frappe.cache().set(_cache_key("progress", user), progress, expires_in_sec=CACHE_TTL)
        frappe.publish_realtime("crm_export_progress", {"progress": progress}, user=user)
        
        # Flush memory every 10 batches
        if processed % 10000 == 0:
            wb.save(path)
            wb = Workbook(write_only=True)
            ws = wb.create_sheet("CRM Deals")
            ws.append(columns)
    
    wb.save(path)
    frappe.cache().set(_cache_key("file", user), path, expires_in_sec=CACHE_TTL * 2)


# -----------------------------
# API: enqueue export
# -----------------------------
@frappe.whitelist()
def enqueue_export():
    frappe.only_for("System Manager")

    user = frappe.session.user

    frappe.cache().delete(_cache_key("progress", user))
    frappe.cache().delete(_cache_key("file", user))

    frappe.enqueue(
        method="your_app.api.crm_deal_export.run_export_job",
        queue="long",
        timeout=3600,
        job_name="CRM Deal XLSX Export",
        user=user
    )

    return {"status": "queued"}


# -----------------------------
# API: progress
# -----------------------------
@frappe.whitelist()
def get_progress():
    user = frappe.session.user

    return {
        "progress": frappe.cache().get(_cache_key("progress", user)) or 0,
        "done": bool(frappe.cache().get(_cache_key("file", user)))
    }


# -----------------------------
# API: download
# -----------------------------
@frappe.whitelist()
def download():
    user = frappe.session.user
    path = frappe.cache().get(_cache_key("file", user))

    if not path:
        frappe.throw("Export not ready")

    with open(path, "rb") as f:
        frappe.response.filename = "crm_deal.xlsx"
        frappe.response.filecontent = f.read()
        frappe.response.type = "binary"
