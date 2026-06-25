# import traceback

# @frappe.whitelist(allow_guest=True)
# def get_zone_from_vertical_master(horse_power, quoted_price, project_type=None):
#     try:
#         hp = float(horse_power)
#         price = float(quoted_price)

#         filters = {}
#         if project_type:
#             filters["project_type"] = project_type

#         verticals = frappe.get_all("Vertical Master", filters=filters, fields=["name"])
#         if not verticals:
#             frappe.log_error("❌ No Vertical Master found", "Zone Debug")
#             return {"zone": "", "error": "No Vertical Master found for given project_type."}

#         frappe.log_error(f"🔍 Found Verticals: {verticals}", "Zone Debug")

#         for vertical in verticals:
#             details = frappe.get_all(
#                 "HP And Zone Details",
#                 filters={"parent": vertical.name},
#                 fields=["zone", "hp", "minimum_rate", "maximum_rate"]
#             )

#             if not details:
#                 frappe.log_error(f"⚠️ No details found for Vertical: {vertical.name}", "Zone Debug")
#                 continue

#             for detail in details:
#                 frappe.log_error(f"📌 Checking Detail: {detail}", "Zone Debug")

#                 if hp_in_range(hp, detail.hp):
#                     frappe.log_error(f"✅ HP MATCHED: {hp} in {detail.hp}", "Zone Debug")

#                     try:
#                         frappe.log_error(f"🔎 Raw Rate Values: {detail.minimum_rate}, {detail.maximum_rate}", "Zone Debug")
#                         min_rate = float(detail.minimum_rate or 0)
#                         max_rate = float(detail.maximum_rate or 0)
#                     except Exception as e:
#                         frappe.log_error(f"❌ Rate Conversion Error: {e}", "Zone Debug")
#                         continue

#                     frappe.log_error(f"💰 Price: {price}, Min: {min_rate}, Max: {max_rate}", "Zone Debug")

#                     if min_rate <= price <= max_rate:
#                         frappe.log_error(f"🎯 Zone Matched: {detail.zone}", "Zone Debug")
#                         return {"zone": detail.zone}
#                 else:
#                     frappe.log_error(f"❌ HP NOT matched for: {hp} in {detail.hp}", "Zone Debug")

#         return {"zone": "", "error": "No matching zone found for given HP and price."}

#     except Exception:
#         tb = traceback.format_exc()
#         frappe.log_error(tb, "get_zone_from_vertical_master Exception")
#         return {"zone": "", "error": "Server error occurred."}


# def hp_in_range(hp_value, hp_str):
#     try:
#         frappe.log_error(f"⚙️ Parsing HP String: {hp_str}", "HP Range Debug")

#         if not hp_str:
#             return False

#         s = hp_str.upper().replace("HP", "").strip()

#         if s.startswith("~"):
#             max_hp = float(s[1:])
#             return hp_value <= max_hp

#         if "-" in s:
#             parts = s.split("-")
#         elif "~" in s:
#             parts = s.split("~")
#         else:
#             return float(s) == hp_value

#         if len(parts) == 2:
#             min_hp = float(parts[0])
#             max_hp = float(parts[1])
#             return min_hp <= hp_value <= max_hp

#         return False

#     except Exception as e:
#         frappe.log_error(f"❌ HP Range Error: {e}", "HP Range Debug")
#         return False
# @frappe.whitelist(allow_guest=True)
# def get_zone_from_vertical_master(horse_power, quoted_price, project_type=None):
#     hp = float(horse_power)
#     price = float(quoted_price)

#     filters = {}
#     if project_type:
#         filters["project_type"] = project_type

#     verticals = frappe.get_all("Vertical Master", filters=filters, fields=["name"])
#     if not verticals:
#         return {"zone": "", "error": "No Vertical Master found for given project_type."}

#     for vertical in verticals:
#         details = frappe.get_all(
#             "HP And Zone Details",
#             filters={"parent": vertical.name},
#             fields=["zone", "hp", "minimum_rate", "maximum_rate"]
#         )

#         if not details:
#             continue

#         for detail in details:
#             if hp_in_range(hp, detail.hp):
#                 min_rate = float(detail.minimum_rate or 0)
#                 max_rate = float(detail.maximum_rate or 0)

#                 if min_rate <= price <= max_rate:
#                     return {"zone": detail.zone}

#     return {"zone": "", "error": "No matching zone found for given HP and price."}


# def hp_in_range(hp_value, hp_str):
#     if not hp_str:
#         return False

#     s = hp_str.upper().replace("HP", "").strip()

#     if s.startswith("~"):
#         max_hp = float(s[1:])
#         return hp_value <= max_hp

#     if "-" in s:
#         parts = s.split("-")
#     elif "~" in s:
#         parts = s.split("~")
#     else:
#         return float(s) == hp_value

#     if len(parts) == 2:
#         min_hp = float(parts[0])
#         max_hp = float(parts[1])
#         return min_hp <= hp_value <= max_hp

#     return False
# ymysql.err.OperationalError: (1054, "Unknown column 'tabVertical Master.project_type' in 'WHERE'")
# Possible source of error: lg (app)



# name1 field undi project_type ledu
import frappe
from frappe.model.document import Document


class VerticalMaster(Document):

    def hp_in_range(hp_value, hp_str):
        if not hp_str:
            return False

        s = hp_str.upper().replace("HP", "").strip()

        if s.startswith("~"):
            max_hp = float(s[1:])
            return hp_value <= max_hp

        if "-" in s:
            parts = s.split("-")
        elif "~" in s:
            parts = s.split("~")
        else:
            return float(s) == hp_value

        if len(parts) == 2:
            min_hp = float(parts[0])
            max_hp = float(parts[1])
            return min_hp <= hp_value <= max_hp

        return False



@frappe.whitelist(allow_guest=True)
def get_zone_from_vertical_master(horse_power, quoted_price, project_type=None):
    hp = float(horse_power)
    price = float(quoted_price)

    filters = {}
    if project_type:
        filters["name1"] = project_type  # 🔄 use 'name1' instead of 'project_type'

    verticals = frappe.get_all("Vertical Master", filters=filters, fields=["name"])
    if not verticals:
        return {"zone": "", "error": "No Vertical Master found for given project_type."}

    for vertical in verticals:
        details = frappe.get_all(
            "HP And Zone Details",
            filters={"parent": vertical.name},
            fields=["zone", "hp", "minimum_rate", "maximum_rate"]
        )

        if not details:
            continue

        for detail in details:
            if hp_in_range(hp, detail.hp):
                min_rate = float(detail.minimum_rate or 0)
                max_rate = float(detail.maximum_rate or 0)

                if min_rate <= price <= max_rate:
                    return {"zone": detail.zone}

    return {"zone": "", "error": "No matching zone found for given HP and price."}


