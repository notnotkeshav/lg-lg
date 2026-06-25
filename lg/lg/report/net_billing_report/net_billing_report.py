# # Copyright (c) 2025, extension and contributors
# # For license information, please see license.txt

# from datetime import datetime
# import frappe
# from calendar import month_abbr

# def execute(filters=None):
#     if not filters:
#         filters = {}

#     # Parse year filters
#     if filters.get("year"):
#         year_filters = [int(y.strip()) for y in filters["year"].split(",") if y.strip().isdigit()]
#     else:
#         # Default current year if not provided
#         year_filters = [datetime.now().year]

#     # Build all months for the selected years
#     month_years = get_month_years(year_filters)

#     # Fetch data
#     data = get_data(filters, month_years)
#     columns = get_columns(month_years)

#     return columns, data


# def get_month_years(year_filters):
#     """Return list of month-year keys like col_jan-2025"""
#     month_years = []
#     for year in year_filters:
#         for m in range(1, 13):
#             key = f"col_{month_abbr[m].lower()}-{year}"
#             month_years.append(key)
#     return month_years


# def get_columns(month_years):
#     """Define fixed report columns + dynamic month columns"""
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
#         {"label": "<b>Total Amount</b>", "fieldname": "amount", "fieldtype": "Float"},
#         {"label": "<b>Payment Frequency</b>", "fieldname": "payment_frequency", "fieldtype": "Select"},
#     ]

#     # Add fixed monthly columns
#     for key in month_years:
#         columns.append({
#             "label": key[4:].title(),
#             "fieldname": key,
#             "fieldtype": "Float",
#             "width": 100
#         })
#     return columns


# def get_data(filters, month_years):
#     """Fetch report data for contracts and billing schedule"""
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

#     # Fetch contracts
#     contracts = frappe.db.get_all("CRM Contract",
#         fields=[
#             "name", "customer", "customer_hc", "amc_year", "start_date", "expiry_date", "project",
#             "amount", "payment_frequency", "from_deal", "from_quote", "total_hp", "deal_type"
#         ],
#         filters=contract_filters
#     )

#     # Map deals
#     deal_ids = [c["from_deal"] for c in contracts if c["from_deal"]]
#     deal_map = {}
#     if deal_ids:
#         deal_data = frappe.db.get_all("CRM Deal", filters={"name": ["in", deal_ids]},
#             fields=["name", "industry", "region", "branch", "hp_under_amc"])
#         deal_map = {d["name"]: d for d in deal_data}

#     # Map quotes
#     quote_ids = [c["from_quote"] for c in contracts if c["from_quote"]]
#     quote_map = {}
#     if quote_ids:
#         quote_data = frappe.db.get_all("CRM Quotation", filters={"name": ["in", quote_ids]},
#             fields=["name", "spec_in_date", "award_date"])
#         quote_map = {q["name"]: q for q in quote_data}

#     # Fetch billing schedule
#     billing_entries = frappe.db.sql("""
#         SELECT parent, billing_date, amount
#         FROM `tabContract Billing Schedule`
#         WHERE parenttype = 'CRM Contract'
#           AND parent IN %(contract_names)s
#     """, {"contract_names": [c["name"] for c in contracts]}, as_dict=True)

#     # Build billing map
#     billing_map = {}
#     for entry in billing_entries:
#         bill_date = entry.billing_date
#         if not bill_date:
#             continue
#         key = f"col_{bill_date.strftime('%b-%Y').lower()}"
#         billing_map.setdefault(entry.parent, {})[key] = entry.amount

#     # Prepare final data
#     data = []
#     for contract in contracts:
#         deal = deal_map.get(contract.from_deal, {})
#         quote = quote_map.get(contract.from_quote, {})

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
#             "total_hp_contract": contract.total_hp or 0,
#             "hp_deal": deal.get("hp_under_amc", 0) or 0,
#             "variance": (contract.total_hp or 0) - (deal.get("hp_under_amc", 0) or 0),
#             "spec_in_date": quote.get("spec_in_date"),
#             "award_date": quote.get("award_date"),
#             "amc_year": contract.amc_year,
#             "start_date": contract.start_date,
#             "expiry_date": contract.expiry_date,
#             "amount": contract.amount,
#             "payment_frequency": contract.payment_frequency
#         }

#         # Ensure all month columns exist (default 0 if missing)
#         for key in month_years:
#             row[key] = billing_map.get(contract.name, {}).get(key, 0)

#         data.append(row)

#     return data

# Copyright (c) 2025, extension and contributors
# For license information, please see license.txt

from datetime import datetime, timedelta
import frappe
from calendar import month_abbr, monthrange

def execute(filters=None):
    if not filters:
        filters = {}

    # Parse year filters
    if filters.get("year"):
        year_filters = [int(y.strip()) for y in filters["year"].split(",") if y.strip().isdigit()]
    else:
        # Default current year if not provided
        year_filters = [datetime.now().year]

    # Build all months for the selected years
    month_years = get_month_years(year_filters)

    # Fetch data
    data = get_data(filters, month_years)
    columns = get_columns(month_years)

    return columns, data


def get_month_years(year_filters):
    """Return list of month-year keys like col_jan-2025"""
    month_years = []
    for year in year_filters:
        for m in range(1, 12+1):
            key = f"col_{month_abbr[m].lower()}-{year}"
            month_years.append(key)
    return month_years


def get_columns(month_years):
    """Define fixed report columns + dynamic month columns"""
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
        {"label": "<b>Total Amount</b>", "fieldname": "amount", "fieldtype": "Float"},
        {"label": "<b>Payment Frequency</b>", "fieldname": "payment_frequency", "fieldtype": "Select"},
        {"label": "<b>Price Rate</b>", "fieldname": "price_rate", "fieldtype": "Float"},
    ]

    # Add fixed monthly columns
    for key in month_years:
        columns.append({
            "label": key[4:].title(),
            "fieldname": key,
            "fieldtype": "Float",
            "width": 100
        })
    return columns


def get_data(filters, month_years):
    """Fetch report data for contracts and calculate monthly billing"""
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

    # Fetch contracts (added price_rate field)
    contracts = frappe.db.get_all("CRM Contract",
        fields=[
            "name", "customer", "customer_hc", "amc_year", "start_date", "expiry_date", "project",
            "amount", "payment_frequency", "from_deal", "from_quote", "total_hp", "deal_type", "price_rate"
        ],
        filters=contract_filters
    )

    # Map deals
    deal_ids = [c["from_deal"] for c in contracts if c["from_deal"]]
    deal_map = {}
    if deal_ids:
        deal_data = frappe.db.get_all("CRM Deal", filters={"name": ["in", deal_ids]},
            fields=["name", "industry", "region", "branch", "hp_under_amc"])
        deal_map = {d["name"]: d for d in deal_data}

    # Map quotes
    quote_ids = [c["from_quote"] for c in contracts if c["from_quote"]]
    quote_map = {}
    if quote_ids:
        quote_data = frappe.db.get_all("CRM Quotation", filters={"name": ["in", quote_ids]},
            fields=["name", "spec_in_date", "award_date"])
        quote_map = {q["name"]: q for q in quote_data}

    # Prepare final data
    data = []
    for contract in contracts:
        deal = deal_map.get(contract.from_deal, {})
        quote = quote_map.get(contract.from_quote, {})

        total_hp_contract = contract.total_hp or 0
        price_rate = contract.price_rate or 0

        # Calculate total contract days
        contract_days = 0
        if contract.start_date and contract.expiry_date:
            contract_days = (contract.expiry_date - contract.start_date).days + 1

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
            "hp_deal": deal.get("hp_under_amc", 0) or 0,
            "variance": total_hp_contract - (deal.get("hp_under_amc", 0) or 0),
            "spec_in_date": quote.get("spec_in_date"),
            "award_date": quote.get("award_date"),
            "amc_year": contract.amc_year,
            "start_date": contract.start_date,
            "expiry_date": contract.expiry_date,
            "amount": contract.amount,
            "payment_frequency": contract.payment_frequency,
            "price_rate": price_rate
        }

        # Calculate monthly values
        for key in month_years:
            # Parse month-year
            month_str = key[4:]  # e.g. jan-2025
            bill_month = datetime.strptime(month_str, "%b-%Y")
            month_start = datetime(bill_month.year, bill_month.month, 1).date()
            month_end = datetime(bill_month.year, bill_month.month, monthrange(bill_month.year, bill_month.month)[1]).date()

            # Find overlap between contract and this month
            if not (contract.start_date and contract.expiry_date and contract_days > 0):
                row[key] = 0
                continue

            overlap_start = max(contract.start_date, month_start)
            overlap_end = min(contract.expiry_date, month_end)

            if overlap_start > overlap_end:
                # No overlap
                row[key] = 0
            else:
                days_in_month = (overlap_end - overlap_start).days + 1
                row[key] = (total_hp_contract * price_rate) * (days_in_month / contract_days)

        data.append(row)

    return data
