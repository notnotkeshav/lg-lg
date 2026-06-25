# # Copyright (c) 2025, extension and contributors
# # For license information, please see license.txt

# from datetime import datetime
# import frappe
# import json

# @frappe.whitelist()
# def execute(filters=None):
#     if not filters:
#         filters = {}

#     # Check for show_in_usd flag
#     show_usd = filters.get("show_in_usd") == 1 or filters.get("show_in_usd") == "1"

#     # Determine exchange rate
#     usd_rate = None
#     if show_usd:
#         try:
#             if filters.get("usd_rate"):
#                 usd_rate = float(filters["usd_rate"])
#             else:
#                 usd_rate = frappe.db.get_value(
#                     "Currency Exchange",
#                     {
#                         "from_currency": "INR",
#                         "to_currency": "USD",
#                         "date": frappe.utils.nowdate()
#                     },
#                     "exchange_rate"
#                 ) or 83.0  # fallback default
#         except:
#             usd_rate = 83.0  # fallback

#     data = get_data(filters, usd_rate if show_usd else None)
#     columns = get_columns(data, show_usd)
#     return columns, data

# def get_columns(data, show_usd=False):
#     columns = [
#         {"label": "<b>Contract ID</b>", "fieldname": "contract_id", "fieldtype": "Link", "options": "CRM Contract"},
#         {"label": "<b>Opportunity Type</b>", "fieldname": "deal_type", "fieldtype": "Data"},
#         {"label": "<b>Project ID</b>", "fieldname": "project", "fieldtype": "Link", "options": "Project"},
#         {"label": "<b>Customer Name</b>", "fieldname": "customer", "fieldtype": "Data"},
#         {"label": "<b>Customer HC</b>", "fieldname": "customer_hc", "fieldtype": "Data"},
#         {"label": "<b>Opportunity ID</b>", "fieldname": "deal_id", "fieldtype": "Link", "options": "CRM Deal"},
#         {"label": "<b>Quote</b>", "fieldname": "quote_id", "fieldtype": "Link", "options": "CRM Quotation"},
#         {"label": "<b>Vertical</b>", "fieldname": "vertical", "fieldtype": "Link", "options": "CRM Industry"},
#         {"label": "<b>Region</b>", "fieldname": "region", "fieldtype": "Data"},
#         {"label": "<b>Branch</b>", "fieldname": "branch", "fieldtype": "Data"},
#         {"label": "<b>HP (Contract)</b>", "fieldname": "total_hp_contract", "fieldtype": "Float"},
#         {"label": "<b>HP as per Deal</b>", "fieldname": "hp_deal", "fieldtype": "Float"},
#         {"label": "<b>Variance</b>", "fieldname": "variance", "fieldtype": "Float"},
#         {"label": "<b>Spec In Date</b>", "fieldname": "spec_in_date", "fieldtype": "Date"},
#         {"label": "<b>Award Date</b>", "fieldname": "award_date", "fieldtype": "Date"},
#         {"label": "<b>AMC Term (Year)</b>", "fieldname": "amc_year", "fieldtype": "Int"},
#         {"label": "<b>Start Date</b>", "fieldname": "start_date", "fieldtype": "Date"},
#         {"label": "<b>Expiry Date</b>", "fieldname": "expiry_date", "fieldtype": "Date"},
#         {"label": "<b>Total Amount (INR)</b>", "fieldname": "amount", "fieldtype": "Float"},
#         {"label": "<b>Payment Frequency</b>", "fieldname": "payment_frequency", "fieldtype": "Select"},
#     ]

#     if show_usd:
#         columns.append({
#             "label": "<b>Total Amount (USD)</b>",
#             "fieldname": "amount_usd",
#             "fieldtype": "Float"
#         })

#     # Add dynamic billing columns
#     month_years = set()
#     for row in data:
#         for key in row:
#             if key.startswith("col_") and not key.endswith("_usd"):
#                 month_years.add(key)

#     sorted_keys = sorted(
#         list(month_years),
#         key=lambda x: datetime.strptime(x[4:], "%b-%Y")
#     )

#     for key in sorted_keys:
#         columns.append({
#             "label": f"{key[4:].title()} (INR)",
#             "fieldname": key,
#             "fieldtype": "Float",
#             "width": 100
#         })
#         if show_usd:
#             columns.append({
#                 "label": f"{key[4:].title()} (USD)",
#                 "fieldname": f"{key}_usd",
#                 "fieldtype": "Float",
#                 "width": 100
#             })

#     return columns

# def get_data(filters, usd_rate=None):
#     year_filters = []
#     if filters.get("year"):
#         year_filters = [int(y.strip()) for y in filters["year"].split(",") if y.strip().isdigit()]

#     contract_filters = {
#         "deal_type": ["!=", "Sales"]
#     }
#     if filters.get("customer"):
#         contract_filters["customer"] = filters["customer"]
#     if filters.get("project"):
#         contract_filters["project"] = filters["project"]
#     if filters.get("vertical"):
#         contract_filters["industry"] = filters["vertical"]
#     if filters.get("deal_type"):
#         contract_filters["deal_type"] = filters["deal_type"]

#     contracts = frappe.db.get_all("CRM Contract",
#         fields=[
#             "name", "customer", "customer_hc", "amc_year", "start_date", "expiry_date", "project",
#             "amount", "payment_frequency", "from_deal", "from_quote", "total_hp", "deal_type"
#         ],
#         filters=contract_filters)

#     deal_ids = [c["from_deal"] for c in contracts if c["from_deal"]]
#     deal_map = {}
#     if deal_ids:
#         deal_data = frappe.db.get_all("CRM Deal", filters={"name": ["in", deal_ids]},
#             fields=["name", "industry", "region", "branch", "hp_under_amc"])
#         deal_map = {d["name"]: d for d in deal_data}

#     # region/branch filters
#     if filters.get("region") or filters.get("branch"):
#         contracts = [
#             c for c in contracts
#             if (not filters.get("region") or deal_map.get(c["from_deal"], {}).get("region") == filters["region"]) and
#                (not filters.get("branch") or deal_map.get(c["from_deal"], {}).get("branch") == filters["branch"])
#         ]

#     quote_ids = [c["from_quote"] for c in contracts if c["from_quote"]]
#     quote_map = {}
#     if quote_ids:
#         quote_data = frappe.db.get_all("CRM Quotation", filters={"name": ["in", quote_ids]},
#             fields=["name", "spec_in_date", "award_date"])
#         quote_map = {q["name"]: q for q in quote_data}

#     billing_entries = frappe.db.sql("""
#         SELECT parent, billing_date, amount
#         FROM `tabContract Billing Schedule`
#         WHERE parenttype = 'CRM Contract'
#           AND parent IN %(contract_names)s
#     """, {"contract_names": [c["name"] for c in contracts]}, as_dict=True)

#     billing_map = {}
#     for entry in billing_entries:
#         bill_date = entry.billing_date
#         if not bill_date:
#             continue
#         if year_filters and bill_date.year not in year_filters:
#             continue
#         key = f"col_{bill_date.strftime('%b-%Y').lower()}"
#         billing_map.setdefault(entry.parent, {})[key] = entry.amount

#     data = []
#     for contract in contracts:
#         deal = deal_map.get(contract.from_deal, {})
#         quote = quote_map.get(contract.from_quote, {})

#         total_hp_contract = contract.total_hp or 0
#         hp_deal = deal.get("hp_under_amc", 0) or 0
#         variance = total_hp_contract - hp_deal

#         row = {
#             "contract_id": contract.name,
#             "customer": contract.customer,
#             "customer_hc": contract.customer_hc,
#             "project": contract.project,
#             "deal_type": contract.deal_type,
#             "deal_id": contract.from_deal,
#             "quote_id": contract.from_quote,
#             "vertical": deal.get("industry"),
#             "region": deal.get("region"),
#             "branch": deal.get("branch"),
#             "total_hp_contract": total_hp_contract,
#             "hp_deal": hp_deal,
#             "variance": variance,
#             "spec_in_date": quote.get("spec_in_date"),
#             "award_date": quote.get("award_date"),
#             "amc_year": contract.amc_year,
#             "start_date": contract.start_date,
#             "expiry_date": contract.expiry_date,
#             "amount": contract.amount,
#             "payment_frequency": contract.payment_frequency
#         }

#         if usd_rate:
#             row["amount_usd"] = round((contract.amount or 0) / usd_rate, 2)

#         monthly = billing_map.get(contract.name, {})
#         for k, v in monthly.items():
#             row[k] = v
#             if usd_rate:
#                 row[f"{k}_usd"] = round(v / usd_rate, 2)

#         data.append(row)

#     return data


# Copyright (c) 2025, extension and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
import json

@frappe.whitelist()
def execute(filters=None):
    if not filters:
        filters = {}

    # Check for show_in_usd flag
    show_usd = filters.get("show_in_usd") == 1 or filters.get("show_in_usd") == "1"

    # Preload exchange rates by month-year
    exchange_rate_map = {}
    if show_usd:
        exchange_rate_map = get_month_year_rates()

    data = get_data(filters, exchange_rate_map if show_usd else None)
    columns = get_columns(data, show_usd)
    return columns, data


def get_month_year_rates():
    """Fetch INR→USD rates grouped by month-year from Currency Exchange"""
    rates = frappe.db.get_all(
        "Currency Exchange",
        filters={"from_currency": "USD", "to_currency": "INR"},
        fields=["date", "exchange_rate"]
    )
    rate_map = {}
    for r in rates:
        dt = r.date
        month_year = (dt.month, dt.year)
        # if multiple entries in same month, pick the latest date
        if month_year not in rate_map or r.date > rate_map[month_year]["date"]:
            rate_map[month_year] = {"date": dt, "rate": r.exchange_rate}
    # simplify to month_year → rate
    return {k: v["rate"] for k, v in rate_map.items()}


def get_columns(data, show_usd=False):
    columns = [
        {"label": "<b>Contract ID</b>", "fieldname": "contract_id", "fieldtype": "Link", "options": "CRM Contract"},
        {"label": "<b>Opportunity Type</b>", "fieldname": "deal_type", "fieldtype": "Data"},
        {"label": "<b>Project ID</b>", "fieldname": "project", "fieldtype": "Link", "options": "Project"},
        {"label": "<b>Customer Name</b>", "fieldname": "customer", "fieldtype": "Data"},
        {"label": "<b>Customer HC</b>", "fieldname": "customer_hc", "fieldtype": "Data"},
        {"label": "<b>Opportunity ID</b>", "fieldname": "deal_id", "fieldtype": "Link", "options": "CRM Deal"},
        {"label": "<b>Quote</b>", "fieldname": "quote_id", "fieldtype": "Link", "options": "CRM Quotation"},
        {"label": "<b>Vertical</b>", "fieldname": "vertical", "fieldtype": "Link", "options": "CRM Industry"},
        {"label": "<b>Region</b>", "fieldname": "region", "fieldtype": "Data"},
        {"label": "<b>Branch</b>", "fieldname": "branch", "fieldtype": "Data"},
        {"label": "<b>HP (Contract)</b>", "fieldname": "total_hp_contract", "fieldtype": "Float"},
        {"label": "<b>HP as per Deal</b>", "fieldname": "hp_deal", "fieldtype": "Float"},
        {"label": "<b>Variance</b>", "fieldname": "variance", "fieldtype": "Float"},
        {"label": "<b>Spec In Date</b>", "fieldname": "spec_in_date", "fieldtype": "Date"},
        {"label": "<b>Award Date</b>", "fieldname": "award_date", "fieldtype": "Date"},
        {"label": "<b>AMC Term (Year)</b>", "fieldname": "amc_year", "fieldtype": "Int"},
        {"label": "<b>Start Date</b>", "fieldname": "start_date", "fieldtype": "Date"},
        {"label": "<b>Expiry Date</b>", "fieldname": "expiry_date", "fieldtype": "Date"},
        {"label": "<b>Total Amount (INR)</b>", "fieldname": "amount", "fieldtype": "Float"},
        {"label": "<b>Payment Frequency</b>", "fieldname": "payment_frequency", "fieldtype": "Select"},
    ]

    if show_usd:
        columns.append({
            "label": "<b>Total Amount (USD)</b>",
            "fieldname": "amount_usd",
            "fieldtype": "Float"
        })

    # Add dynamic billing columns
    month_years = set()
    for row in data:
        for key in row:
            if key.startswith("col_") and not key.endswith("_usd"):
                month_years.add(key)

    sorted_keys = sorted(
        list(month_years),
        key=lambda x: datetime.strptime(x[4:], "%b-%Y")
    )

    for key in sorted_keys:
        columns.append({
            "label": f"{key[4:].title()} (INR)",
            "fieldname": key,
            "fieldtype": "Float",
            "width": 150
        })
        if show_usd:
            columns.append({
                "label": f"{key[4:].title()} (USD)",
                "fieldname": f"{key}_usd",
                "fieldtype": "Float",
                "width": 150
            })

    return columns


def get_data(filters, exchange_rate_map=None):
    year_filters = []
    if filters.get("year"):
        year_filters = [int(y.strip()) for y in filters["year"].split(",") if y.strip().isdigit()]

    contract_filters = {
        "deal_type": ["!=", "Sales"]
    }
    if filters.get("customer"):
        contract_filters["customer"] = filters["customer"]
    if filters.get("project"):
        contract_filters["project"] = filters["project"]
    if filters.get("vertical"):
        contract_filters["industry"] = filters["vertical"]
    if filters.get("deal_type"):
        contract_filters["deal_type"] = filters["deal_type"]

    contracts = frappe.db.get_all("CRM Contract",
        fields=[
            "name", "customer", "customer_hc", "amc_year", "start_date", "expiry_date", "project",
            "amount", "payment_frequency", "from_deal", "from_quote", "total_hp", "deal_type"
        ],
        filters=contract_filters)

    deal_ids = [c["from_deal"] for c in contracts if c["from_deal"]]
    deal_map = {}
    if deal_ids:
        deal_data = frappe.db.get_all("CRM Deal", filters={"name": ["in", deal_ids]},
            fields=["name", "industry", "region", "branch", "hp_under_amc"])
        deal_map = {d["name"]: d for d in deal_data}

    # region/branch filters
    if filters.get("region") or filters.get("branch"):
        contracts = [
            c for c in contracts
            if (not filters.get("region") or deal_map.get(c["from_deal"], {}).get("region") == filters["region"]) and
               (not filters.get("branch") or deal_map.get(c["from_deal"], {}).get("branch") == filters["branch"])
        ]

    quote_ids = [c["from_quote"] for c in contracts if c["from_quote"]]
    quote_map = {}
    if quote_ids:
        quote_data = frappe.db.get_all("CRM Quotation", filters={"name": ["in", quote_ids]},
            fields=["name", "spec_in_date", "award_date"])
        quote_map = {q["name"]: q for q in quote_data}

    billing_entries = frappe.db.sql("""
        SELECT parent, billing_date, amount
        FROM `tabContract Billing Schedule`
        WHERE parenttype = 'CRM Contract'
          AND parent IN %(contract_names)s
    """, {"contract_names": [c["name"] for c in contracts]}, as_dict=True)

    billing_map = {}
    for entry in billing_entries:
        bill_date = entry.billing_date
        if not bill_date:
            continue
        if year_filters and bill_date.year not in year_filters:
            continue
        key = f"col_{bill_date.strftime('%b-%Y').lower()}"
        billing_map.setdefault(entry.parent, {})[key] = {
            "amount": entry.amount,
            "date": bill_date
        }

    data = []
    for contract in contracts:
        deal = deal_map.get(contract.from_deal, {})
        quote = quote_map.get(contract.from_quote, {})

        total_hp_contract = contract.total_hp or 0
        hp_deal = deal.get("hp_under_amc", 0) or 0
        variance = total_hp_contract - hp_deal

        row = {
            "contract_id": contract.name,
            "customer": contract.customer,
            "customer_hc": contract.customer_hc,
            "project": contract.project,
            "deal_type": contract.deal_type,
            "deal_id": contract.from_deal,
            "quote_id": contract.from_quote,
            "vertical": deal.get("industry"),
            "region": deal.get("region"),
            "branch": deal.get("branch"),
            "total_hp_contract": total_hp_contract,
            "hp_deal": hp_deal,
            "variance": variance,
            "spec_in_date": quote.get("spec_in_date"),
            "award_date": quote.get("award_date"),
            "amc_year": contract.amc_year,
            "start_date": contract.start_date,
            "expiry_date": contract.expiry_date,
            "amount": contract.amount,
            "payment_frequency": contract.payment_frequency
        }
   
        # Contract amount conversion (use start_date month-year rate)
        if exchange_rate_map and contract.start_date:
            month_year = (contract.start_date.month, contract.start_date.year)
            rate = exchange_rate_map.get(month_year, 83.0)
            row["amount_usd"] = round((contract.amount or 0) / rate, 2)

        # Monthly billing conversion
        monthly = billing_map.get(contract.name, {})
        for k, v in monthly.items():
            row[k] = v["amount"]
            if exchange_rate_map:
                bill_date = v["date"]
                month_year = (bill_date.month, bill_date.year)
                rate = exchange_rate_map.get(month_year, 83.0)
                row[f"{k}_usd"] = round(v["amount"] / rate, 2)

        data.append(row)

    return data
