# import frappe
# from datetime import datetime, date
# from dateutil.relativedelta import relativedelta
# from math import ceil

# @frappe.whitelist()
# def execute(filters=None):
#     if not filters:
#         filters = {}

#     # Fetch data
#     data = get_data(filters)

#     # Process payments based on the frequency and split data by year, month, and Contract ID
#     data = process_payment_distribution(data)

#     # Generate columns dynamically based on data
#     columns = get_columns(data)

#     # Prepare chart data
#     chart = get_chart_data(data)

#     return columns, data, None, chart


# def get_columns(data):
#     columns = [
#         {"label": "<b>Customer Name</b>", "fieldname": "customer", "fieldtype": "Data"},
#         {"label": "<b>Customer HC</b>", "fieldname": "customer_hc", "fieldtype": "Data"},
#         {"label": "<b>Contract ID</b>", "fieldname": "name", "fieldtype": "Link", "options": "CRM Contract"},
#         {"label": "<b>Contract From</b>", "fieldname": "contract_from", "fieldtype": "Data"},
#         {"label": "<b>AMC</b>", "fieldname": "amc", "fieldtype": "Data"},
#         {"label": "<b>Start Date</b>", "fieldname": "start_date", "fieldtype": "Date"},
#         {"label": "<b>Expiry Date</b>", "fieldname": "expiry_date", "fieldtype": "Date"},
#         {"label": "<b>Total Amount</b>", "fieldname": "amount", "fieldtype": "Float"},
#         {"label": "<b>Payment Frequency</b>", "fieldname": "payment_frequency", "fieldtype": "Select"},
#         {"label": "<b>Months</b>", "fieldname": "months", "fieldtype": "Int", "width": 100},  # Number of months column
#     ]

#     # Append year and months dynamically
#     months = [
#         "<center><b>January</b></center>", "<center><b>February</b></center>", "<center><b>March</b></center>",
#         "<center><b>April</b></center>", "<center><b>May</b></center>", "<center><b>June</b><center>",
#         "<center><b>July</center>", "August", "September", "October", "November", "December"
#     ]

#     columns.append({"label": "<b>Year</b>", "fieldname": "year", "fieldtype": "Int", "width": 100})
#     for month in months:
#         columns.append({"label": month, "fieldname": month.lower(), "fieldtype": "Float", "width": 100})

#     return columns


# def process_payment_distribution(data):
#     processed_data = []  # To store rows split by Contract ID and year

#     for row in data:
#         if not row.get("start_date") or not row.get("expiry_date"):
#             continue

#         # Ensure dates are in the correct format
#         start_date = row["start_date"]
#         expiry_date = row["expiry_date"]

#         if isinstance(start_date, (datetime, date)):
#             start_date = datetime.combine(start_date, datetime.min.time())
#         if isinstance(expiry_date, (datetime, date)):
#             expiry_date = datetime.combine(expiry_date, datetime.min.time())

#         # Calculate the number of months
#         row["months"] = calculate_months(start_date, expiry_date)

#         # Convert total_amount to a float for calculations
#         try:
#             total_amount = float(row.get("amount", 0))
#         except ValueError:
#             total_amount = 0  # Fallback if conversion fails

#         frequency = row.get("payment_frequency", "").lower()
#         distributed_amount = 0  # Track the total amount distributed

#         # Process payments based on frequency and segregate by Contract ID
#         current_date = start_date
#         year_rows = {}

#         if frequency == "monthly":
#             monthly_amount = total_amount / row["months"] if row["months"] else 0

#             while current_date <= expiry_date and abs(distributed_amount - total_amount) > 1:
#                 year = current_date.year
#                 month_key = current_date.strftime("%B").lower()

#                 if year not in year_rows:
#                     year_rows[year] = create_year_row(row, year)

#                 year_rows[year][month_key] = monthly_amount  # Assign the payment
#                 distributed_amount += monthly_amount
#                 current_date += relativedelta(months=1)  # Move to the next month

#         elif frequency == "quarterly":
#             quarters = ceil(row["months"] / 3)
#             quarterly_amount = total_amount / quarters if quarters else 0

#             while current_date <= expiry_date and abs(distributed_amount - total_amount) > 1:
#                 year = current_date.year
#                 month_key = current_date.strftime("%B").lower()

#                 if year not in year_rows:
#                     year_rows[year] = create_year_row(row, year)

#                 year_rows[year][month_key] = quarterly_amount  # Assign the payment
#                 distributed_amount += quarterly_amount
#                 current_date += relativedelta(months=3)  # Move to the next quarter

#         elif frequency == "semi-annually":
#             half_years = ceil(row["months"] / 6)
#             semi_annual_amount = total_amount / half_years if half_years else 0

#             while current_date <= expiry_date and abs(distributed_amount - total_amount) > 1:
#                 year = current_date.year
#                 month_key = current_date.strftime("%B").lower()

#                 if year not in year_rows:
#                     year_rows[year] = create_year_row(row, year)

#                 year_rows[year][month_key] = semi_annual_amount  # Assign the payment
#                 distributed_amount += semi_annual_amount
#                 current_date += relativedelta(months=6)  # Move to the next half-year

#         elif frequency == "annually":
#             years = ceil(row["months"] / 12)
#             annual_amount = total_amount / years if years else 0

#             while current_date <= expiry_date and abs(distributed_amount - total_amount) > 1:
#                 year = current_date.year
#                 month_key = current_date.strftime("%B").lower()

#                 if year not in year_rows:
#                     year_rows[year] = create_year_row(row, year)

#                 year_rows[year][month_key] = annual_amount  # Assign the payment
#                 distributed_amount += annual_amount
#                 current_date += relativedelta(years=1)  # Move to the next year

#         # Replace zeroes with None to indicate null values
#         for year_row in year_rows.values():
#             for month in [
#                 "january", "february", "march", "april", "may", "june",
#                 "july", "august", "september", "october", "november", "december"
#             ]:
#                 if year_row[month] == 0:
#                     year_row[month] = None

#         # Append year-wise rows for the current Contract ID
#         processed_data.extend(year_rows.values())

#     return processed_data


# def calculate_months(start_date, expiry_date):
#     """
#     Calculate the number of months between start_date and expiry_date.
#     """
#     return (expiry_date.year - start_date.year) * 12 + expiry_date.month - start_date.month + 1


# def create_year_row(row, year):
#     """
#     Create a new row for a specific year, initialized with None for all months.
#     """
#     return {
#         **row,  # Copy all other details
#         "year": year,
#         **{m.lower(): None for m in [
#             "January", "February", "March", "April", "May", "June",
#             "July", "August", "September", "October", "November", "December"
#         ]}
#     }

# def get_conditions(filters):
#     conditions = []
#     values = filters or {}

#     # if filters.get("start_date"):
#     #     conditions.append("start_date >= %(start_date)s")
#     # if filters.get("end_date"):
#     #     conditions.append("expiry_date <= %(end_date)s")
#     if 'customer' in filters:
#         conditions.append("customer = %(customer)s")
#     # if 'contract_from' in filters:
#     #     conditions.append("contract_from = %(contract_from)s")
#     if 'payment_frequency' in filters:
#         conditions.append("payment_frequency = %(payment_frequency)s")
#     # if 'year' in filters:
#     #     conditions.append("year = %(year)s")
    
#     return " AND ".join(conditions) if conditions else "", values

# def get_data(filters):
#     conditions, values = get_conditions(filters)
#     conditions = f"WHERE {conditions}" if conditions else ""
#     query = f"""
#         SELECT 
#             customer,
#             customer_hc,
#             name,
#             CASE 
#                 WHEN contract_from = 'CRM Deal' THEN from_deal 
#                 ELSE from_quote 
#             END AS contract_from,
#             amc,
#             start_date,
#             expiry_date,
#             amount,
#             payment_frequency
#         FROM 
#             `tabCRM Contract`
#         {conditions}
#     """
#     return frappe.db.sql(query, filters, as_dict=True)

# def get_chart_data(data):
#     """Prepare data for the line chart"""
#     months = [
#         "january", "february", "march", "april", "may", "june",
#         "july", "august", "september", "october", "november", "december"
#     ]
    
#     # Initialize monthly totals
#     monthly_totals = {month: 0 for month in months}
    
#     # Sum up amounts for each month
#     for row in data:
#         for month in months:
#             if row.get(month):
#                 monthly_totals[month] += row[month]
    
#     # Format data for chart
#     chart = {
#         "data": {
#             "labels": [month.capitalize() for month in months],
#             "datasets": [
#                 {
#                     "name": "Monthly Revenue",
#                     "values": [monthly_totals[month] for month in months]
#                 }
#             ]
#         },
#         "type": "line",
#         "colors": ["#2490ef"],  # Blue color for the line
#         "lineOptions": {
#             "regionFill": 1,  # Enable area fill below the line
#             "hideDots": 0,    # Show data points
#             "heatline": 0,    # Disable heatline
#             "spline": 1,      # Enable smooth curve
#             "dotSize":5       # Dotsize
#         },
#         "axisOptions": {
#             "xAxisMode": "tick",
#             "yAxisMode": "tick",
#             "xIsSeries": 1
#         }
#     }
    
#     return chart

# import frappe


# @frappe.whitelist()
# def execute(filters=None):
#     if not filters:
#         filters = {}

#     data = get_data(filters)

#     # Process payments based on the frequency and split data by year, month, and Contract ID
#     data = process_payment_distribution(data)

#     # Generate columns dynamically based on data
#     columns = get_columns(data)

#     # Prepare chart data
#     chart = get_chart_data(data)

#     return columns, data, None, chart

# def execute(filters=None):
#     filters = filters or {}

#     conditions = []
#     sql_filters = {}

#     if filters.get("customer"):
#         conditions.append("c.customer = %(customer)s")
#         sql_filters["customer"] = filters["customer"]

#     if filters.get("project"):
#         conditions.append("c.project = %(project)s")
#         sql_filters["project"] = filters["project"]

#     if filters.get("payment_frequency"):
#         conditions.append("c.payment_frequency = %(payment_frequency)s")
#         sql_filters["payment_frequency"] = filters["payment_frequency"]

#     year = filters.get("year")
#     if year:
#         conditions.append("YEAR(b.billing_date) >= %(year)s")
#         sql_filters["year"] = int(year)

#     where_clause = " AND ".join(conditions)
#     if where_clause:
#         where_clause = "WHERE " + where_clause

#     columns = [
#         {"label": "Year", "fieldname": "year", "fieldtype": "Int", "width": 80},
#         {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "CRM Organization", "width": 150},
#         {"label": "Project", "fieldname": "project", "fieldtype": "Data", "width": 150},
#         {"label": "Contract", "fieldname": "contract", "fieldtype": "Link", "options": "CRM Contract", "width": 150},
#         {"label": "Payment Frequency", "fieldname": "Payment Frequency", "fieldtype": "Data", "width": 150},
#     ]

#     # Month columns
#     month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
#                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
#     for m in month_names:
#         columns.append({
#             "label": m,
#             "fieldname": m.lower(),
#             "fieldtype": "Currency",
#             "width": 100
#         })

#     query = f"""
#         SELECT 
#             YEAR(b.billing_date) AS year,
#             c.customer AS customer,
#             c.project AS project,
#             c.name AS contract,
#             c.payment_frequency AS `Payment Frequency`,
#             SUM(CASE WHEN MONTH(b.billing_date) = 1 THEN b.amount ELSE 0 END) AS jan,
#             SUM(CASE WHEN MONTH(b.billing_date) = 2 THEN b.amount ELSE 0 END) AS feb,
#             SUM(CASE WHEN MONTH(b.billing_date) = 3 THEN b.amount ELSE 0 END) AS mar,
#             SUM(CASE WHEN MONTH(b.billing_date) = 4 THEN b.amount ELSE 0 END) AS apr,
#             SUM(CASE WHEN MONTH(b.billing_date) = 5 THEN b.amount ELSE 0 END) AS may,
#             SUM(CASE WHEN MONTH(b.billing_date) = 6 THEN b.amount ELSE 0 END) AS jun,
#             SUM(CASE WHEN MONTH(b.billing_date) = 7 THEN b.amount ELSE 0 END) AS jul,
#             SUM(CASE WHEN MONTH(b.billing_date) = 8 THEN b.amount ELSE 0 END) AS aug,
#             SUM(CASE WHEN MONTH(b.billing_date) = 9 THEN b.amount ELSE 0 END) AS sep,
#             SUM(CASE WHEN MONTH(b.billing_date) = 10 THEN b.amount ELSE 0 END) AS oct,
#             SUM(CASE WHEN MONTH(b.billing_date) = 11 THEN b.amount ELSE 0 END) AS nov,
#             SUM(CASE WHEN MONTH(b.billing_date) = 12 THEN b.amount ELSE 0 END) AS `dec`
#         FROM 
#             `tabContract Billing Schedule` b
#         JOIN 
#             `tabCRM Contract` c ON b.parent = c.name
#         {where_clause}
#         GROUP BY 
#             YEAR(b.billing_date), c.customer, c.project, c.name
#         ORDER BY 
#             YEAR(b.billing_date), c.customer, c.project
#     """

#     data = frappe.db.sql(query, sql_filters, as_dict=1)
#     return columns, data

# def get_chart_data(data):
#     """Prepare data for the line chart showing monthly revenue trend"""

#     # Match fieldnames from SQL: jan, feb, mar, ...
#     months_abbr = [
#         "jan", "feb", "mar", "apr", "may", "jun",
#         "jul", "aug", "sep", "oct", "nov", "dec"
#     ]

#     month_labels = [
#         "January", "February", "March", "April", "May", "June",
#         "July", "August", "September", "October", "November", "December"
#     ]
    
#     # Initialize totals
#     monthly_totals = {month: 0 for month in months_abbr}
    
#     # Sum amounts for each month across all records
#     for row in data:
#         for month in months_abbr:
#             if row.get(month):
#                 monthly_totals[month] += row[month]
    
#     # Prepare chart
#     chart = {
#         "data": {
#             "labels": month_labels,
#             "datasets": [
#                 {
#                     "name": "Monthly Revenue",
#                     "values": [monthly_totals[m] for m in months_abbr]
#                 }
#             ]
#         },
#         "type": "line",
#         "colors": ["#2490ef"],
#         "lineOptions": {
#             "regionFill": 1,
#             "hideDots": 0,
#             "heatline": 1, 
#             "spline": 1,
#             "dotSize": 4
#         },
#         "axisOptions": {
#             "xAxisMode": "tick",
#             "yAxisMode": "tick",
#             "xIsSeries": 1
#         }
#     }

#     return chart

import frappe

# @frappe.whitelist()
# def execute(filters=None):
#     filters = frappe._dict(filters or {})

#     columns, data = get_report_data(filters)
#     chart = get_chart_data(data)

#     return columns, data, None, chart

@frappe.whitelist()
def execute(filters=None):
    import json

    if isinstance(filters, str):
        filters = json.loads(filters)

    filters = filters or {}

    columns, data = get_report_data(filters)
    chart = get_chart_data(data)

    return columns, data, None, chart


def get_report_data(filters):
    conditions = []
    sql_filters = {}

    if filters.get("customer"):
        conditions.append("c.customer = %(customer)s")
        sql_filters["customer"] = filters["customer"]

    if filters.get("project"):
        conditions.append("c.project = %(project)s")
        sql_filters["project"] = filters["project"]

    if filters.get("payment_frequency"):
        conditions.append("c.payment_frequency = %(payment_frequency)s")
        sql_filters["payment_frequency"] = filters["payment_frequency"]

    if filters.get("year"):
        conditions.append("YEAR(b.billing_date) >= %(year)s")
        sql_filters["year"] = int(filters["year"])

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    columns = [
        {"label": "Year", "fieldname": "year", "fieldtype": "Int", "width": 80},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "CRM Organization", "width": 150},
        {"label": "Project", "fieldname": "project", "fieldtype": "Data", "width": 150},
        {"label": "Contract", "fieldname": "contract", "fieldtype": "Link", "options": "CRM Contract", "width": 150},
        {"label": "Payment Frequency", "fieldname": "payment_frequency", "fieldtype": "Data", "width": 150},
        {"label": "Total Amount", "fieldname": "Amount", "fieldtype": "Currency", "width": 150},
        {"label": "Exchange Rate", "fieldname": "Exchange Rate", "fieldtype": "Float", "width": 100},
        {"label": "Total in USD", "fieldname": "Amount in USD", "fieldtype": "Currency", "width": 150},
    ]

    # Month columns
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for m in month_names:
        columns.append({
            "label": m,
            "fieldname": m.lower(),
            "fieldtype": "Currency",
            "width": 100
        })

    query = f"""
        SELECT 
            YEAR(b.billing_date) AS year,
            c.customer AS customer,
            c.project AS project,
            c.name AS contract,
            c.amount AS Amount,
            c.conversion_rate AS `Exchange Rate`,
            c.total_usd AS `Amount in USD`,
            c.payment_frequency AS payment_frequency,
            SUM(CASE WHEN MONTH(b.billing_date) = 1 THEN b.amount ELSE 0 END) AS jan,
            SUM(CASE WHEN MONTH(b.billing_date) = 2 THEN b.amount ELSE 0 END) AS feb,
            SUM(CASE WHEN MONTH(b.billing_date) = 3 THEN b.amount ELSE 0 END) AS mar,
            SUM(CASE WHEN MONTH(b.billing_date) = 4 THEN b.amount ELSE 0 END) AS apr,
            SUM(CASE WHEN MONTH(b.billing_date) = 5 THEN b.amount ELSE 0 END) AS may,
            SUM(CASE WHEN MONTH(b.billing_date) = 6 THEN b.amount ELSE 0 END) AS jun,
            SUM(CASE WHEN MONTH(b.billing_date) = 7 THEN b.amount ELSE 0 END) AS jul,
            SUM(CASE WHEN MONTH(b.billing_date) = 8 THEN b.amount ELSE 0 END) AS aug,
            SUM(CASE WHEN MONTH(b.billing_date) = 9 THEN b.amount ELSE 0 END) AS sep,
            SUM(CASE WHEN MONTH(b.billing_date) = 10 THEN b.amount ELSE 0 END) AS oct,
            SUM(CASE WHEN MONTH(b.billing_date) = 11 THEN b.amount ELSE 0 END) AS nov,
            SUM(CASE WHEN MONTH(b.billing_date) = 12 THEN b.amount ELSE 0 END) AS `dec`
        FROM 
            `tabContract Billing Schedule` b
        JOIN 
            `tabCRM Contract` c ON b.parent = c.name
        {where_clause}
        GROUP BY 
            YEAR(b.billing_date), c.customer, c.project, c.name
        ORDER BY 
            YEAR(b.billing_date), c.customer, c.project
    """

    data = frappe.db.sql(query, sql_filters, as_dict=1)
    return columns, data

def get_chart_data(data):
    """Prepare line chart data showing monthly revenue trend"""

    # SQL field names for months
    months_abbr = [
        "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "oct", "nov", "dec"
    ]

    month_labels = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Sum totals across months
    monthly_totals = {month: 0 for month in months_abbr}
    for row in data:
        for month in months_abbr:
            if row.get(month):
                monthly_totals[month] += row[month]

    chart = {
        "data": {
            "labels": month_labels,
            "datasets": [
                {
                    "name": "Monthly Revenue",
                    "values": [monthly_totals[m] for m in months_abbr]
                }
            ]
        },
        "type": "line",
        "colors": ["#2490ef"],
        "lineOptions": {
            "regionFill": 1,
            "hideDots": 0,
            "heatline": 1,
            "spline": 1,
            "dotSize": 4
        },
        "axisOptions": {
            "xAxisMode": "tick",
            "yAxisMode": "tick",
            "xIsSeries": 1
        }
    }

    return chart
