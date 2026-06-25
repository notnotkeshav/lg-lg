import frappe
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from math import ceil


def execute(filters=None):
    if not filters:
        filters = {}

    # Fetch data
    data = get_data(filters)

    # Process payments based on the frequency and split data by year, month, and Contract ID
    data = process_payment_distribution(data)

    # Generate columns dynamically based on data
    columns = get_columns(data)

    
    return columns, data, None

def get_columns(data):
    columns = [
        {"label": "<b>Customer Name</b>", "fieldname": "customer", "fieldtype": "Data"},
        {"label": "Customer HC", "fieldname": "customer_hc", "fieldtype": "Data"},
        {"label": "Industry", "fieldname": "industry", "fieldtype": "data","width":120},
        {"label": "Region", "fieldname": "region", "fieldtype": "data","width":120},
        {"label": "Branch", "fieldname": "branch", "fieldtype": "data","width":120},
        {"label": "Branch Head", "fieldname": "branch_head", "fieldtype": "data","width":200},
        {"label": "Contract ID", "fieldname": "name", "fieldtype": "Link", "options": "CRM Contract"},
        {"label": "Contract From", "fieldname": "contract_from", "fieldtype": "Data"},
        {"label": "AMC", "fieldname": "amc", "fieldtype": "Data"},
        {"label": "Start Date", "fieldname": "start_date", "fieldtype": "Date"},
        {"label": "Expiry Date", "fieldname": "expiry_date", "fieldtype": "Date"},
        {"label": "Total Amount", "fieldname": "amount", "fieldtype": "Float"},
        {"label": "Payment Frequency", "fieldname": "payment_frequency", "fieldtype": "Select"},
        {"label": "Months", "fieldname": "months", "fieldtype": "Int", "width": 100},  # Number of months column
    ]

    # Append year and months dynamically
    months = [
        "<b>January</b>", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    columns.append({"label": "Year", "fieldname": "year", "fieldtype": "Int", "width": 100})
    for month in months:
        columns.append({"label": month, "fieldname": month.lower(), "fieldtype": "Float", "width": 100})

    return columns

def process_payment_distribution(data):
    processed_data = []  # To store rows split by Contract ID and year

    for row in data:
        if not row.get("start_date") or not row.get("expiry_date"):
            continue

        # Ensure dates are in the correct format
        start_date = row["start_date"]
        expiry_date = row["expiry_date"]

        if isinstance(start_date, (datetime, date)):
            start_date = datetime.combine(start_date, datetime.min.time())
        if isinstance(expiry_date, (datetime, date)):
            expiry_date = datetime.combine(expiry_date, datetime.min.time())

        # Calculate the number of months
        row["months"] = calculate_months(start_date, expiry_date)

        # Convert total_amount to a float for calculations
        try:
            total_amount = float(row.get("amount", 0))
        except ValueError:
            total_amount = 0  # Fallback if conversion fails

        frequency = row.get("payment_frequency", "").lower()
        distributed_amount = 0  # Track the total amount distributed

        # Process payments based on frequency and segregate by Contract ID
        current_date = start_date
        year_rows = {}

        if frequency == "monthly":
            monthly_amount = total_amount / row["months"] if row["months"] else 0

            while current_date <= expiry_date and abs(distributed_amount - total_amount) > 1:
                year = current_date.year
                month_key = current_date.strftime("%B").lower()

                if year not in year_rows:
                    # Include amount only for the first year
                    include_amount = len(year_rows) == 0
                    year_rows[year] = create_year_row(row, year, include_amount)

                year_rows[year][month_key] = monthly_amount  # Assign the payment
                distributed_amount += monthly_amount
                current_date += relativedelta(months=1)  # Move to the next month

        elif frequency == "quarterly":
            quarters = ceil(row["months"] / 3)
            quarterly_amount = total_amount / quarters if quarters else 0

            while current_date <= expiry_date and abs(distributed_amount - total_amount) > 1:
                year = current_date.year
                month_key = current_date.strftime("%B").lower()

                if year not in year_rows:
                    include_amount = len(year_rows) == 0
                    year_rows[year] = create_year_row(row, year, include_amount)

                year_rows[year][month_key] = quarterly_amount  # Assign the payment
                distributed_amount += quarterly_amount
                current_date += relativedelta(months=3)  # Move to the next quarter

        elif frequency == "semi-annually":
            half_years = ceil(row["months"] / 6)
            semi_annual_amount = total_amount / half_years if half_years else 0

            while current_date <= expiry_date and abs(distributed_amount - total_amount) > 1:
                year = current_date.year
                month_key = current_date.strftime("%B").lower()

                if year not in year_rows:
                    include_amount = len(year_rows) == 0
                    year_rows[year] = create_year_row(row, year, include_amount)

                year_rows[year][month_key] = semi_annual_amount  # Assign the payment
                distributed_amount += semi_annual_amount
                current_date += relativedelta(months=6)  # Move to the next half-year

        elif frequency == "annually":
            years = ceil(row["months"] / 12)
            annual_amount = total_amount / years if years else 0

            while current_date <= expiry_date and abs(distributed_amount - total_amount) > 1:
                year = current_date.year
                month_key = current_date.strftime("%B").lower()

                if year not in year_rows:
                    include_amount = len(year_rows) == 0
                    year_rows[year] = create_year_row(row, year, include_amount)

                year_rows[year][month_key] = annual_amount  # Assign the payment
                distributed_amount += annual_amount
                current_date += relativedelta(years=1)  # Move to the next year

        # Replace zeroes with None to indicate null values
        for year_row in year_rows.values():
            for month in [
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ]:
                if year_row[month] == 0:
                    year_row[month] = None

        # Append year-wise rows for the current Contract ID
        processed_data.extend(year_rows.values())

    return processed_data

def calculate_months(start_date, expiry_date):
    """
    Calculate the number of months between start_date and expiry_date.
    """
    return (expiry_date.year - start_date.year) * 12 + expiry_date.month - start_date.month + 1

def create_year_row(row, year, include_amount=True):
    """
    Create a new row for a specific year, initialized with None for all months.
    Optionally include the total amount.
    """
    new_row = {
        **row,  # Copy all other details
        "year": year,
        **{m.lower(): None for m in [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]}
    }
    if not include_amount:
        new_row["amount"] = None  # Set amount to None for non-first years
    return new_row

def get_conditions(filters):
    conditions = []
    values = filters or {}

    if 'customer' in filters:
        conditions.append("customer = %(customer)s")
    if 'payment_frequency' in filters:
        conditions.append("payment_frequency = %(payment_frequency)s")
    if 'industry' in filters:
        conditions.append("industry = %(industry)s")
    if 'region' in filters:
        conditions.append("region = %(region)s")   
    if 'branch' in filters:
        conditions.append("branch = %(branch)s") 
    # if 'branch_head' in filters:
    #     conditions.append("branch_head = %(branch_head)s") 

    return " AND ".join(conditions) if conditions else "", values

def get_data(filters):
    conditions, values = get_conditions(filters)
    conditions = f"WHERE {conditions}" if conditions else ""
    query = f"""
        SELECT 
            c.customer,
            c.customer_hc,
            cu.region,
            cu.industry,
            cu.branch,
            cu.branch_head,
            c.name,
            CASE 
                WHEN c.contract_from = 'CRM Deal' THEN c.from_deal 
                ELSE c.from_quote 
            END AS contract_from,
            c.amc,
            c.start_date,
            c.expiry_date,
            c.amount,
            c.payment_frequency
        FROM 
            `tabCRM Contract` AS c
            JOIN `tabCRM Organization` AS cu 
            ON c.customer_hc=cu.customer_hc
        {conditions}
    """
    return frappe.db.sql(query, filters, as_dict=True)
