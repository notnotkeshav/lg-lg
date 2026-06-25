# Copyright (c) 2025, extension and contributors
# For license information, please see license.txt

# import frappe

# def execute(filters=None):
#     conditions = ""

#     if filters.get("customer"):
#         conditions += " AND c.name = %(customer)s"

#     if filters.get("from_date") and filters.get("to_date"):
#         conditions += " AND ct.start_date BETWEEN %(from_date)s AND %(to_date)s"

#     return get_columns(), get_data(filters, conditions)


# def get_columns():
#     return [
#         {"label": "<b>Customer HC</b>", "fieldname": "customer_hc", "fieldtype": "Data", "width": 120},
#         {"label": "<b>Customer Name</b>", "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
#         {"label": "<b>Total Projects</b>", "fieldname": "total_projects", "fieldtype": "Int", "width": 120},
#         {"label": "<b>Active Projects</b>", "fieldname": "active_projects", "fieldtype": "Int", "width": 140},
#         {"label": "<b>Total Deals</b>", "fieldname": "total_deals", "fieldtype": "Int", "width": 100},
#         {"label": "<b>Active Deals</b>", "fieldname": "active_deals", "fieldtype": "Int", "width": 130},
#         {"label": "<b>Total Quotes</b>", "fieldname": "total_quotes", "fieldtype": "Int", "width": 130},
#         {"label": "<b>Quotes Won</b>", "fieldname": "quotes_won", "fieldtype": "Int", "width": 130},
#         {"label": "<b>Total Contracts</b>", "fieldname": "total_contracts", "fieldtype": "Int", "width": 150},
#         {"label": "<b>Active Contracts</b>", "fieldname": "active_contracts", "fieldtype": "Int", "width": 150},
#     ]


# def get_data(filters, conditions):
#     return frappe.db.sql(f"""
#         SELECT 
#             c.name AS customer_hc,
#             c.organization_name AS customer_name,
#             IFNULL(p.total_projects, 0) AS total_projects,
#             IFNULL(p.active_projects, 0) AS active_projects,
#             IFNULL(d.total_deals, 0) AS total_deals,
#             IFNULL(d.active_deals, 0) AS active_deals,
#             IFNULL(q.total_quotes, 0) AS total_quotes,
#             IFNULL(q.quotes_won, 0) AS quotes_won,
#             IFNULL(ct.total_contracts, 0) AS total_contracts,
#             IFNULL(ct.active_contracts, 0) AS active_contracts

#         FROM `tabCRM Organization` c

#         LEFT JOIN (
#             SELECT 
#                 customer, 
#                 COUNT(name) AS total_projects,
#                 SUM(CASE WHEN status IN ('IN Warranty', 'AMC Active') THEN 1 ELSE 0 END) AS active_projects
#             FROM `tabProject`
#             GROUP BY customer
#         ) p ON p.customer = c.name

#         LEFT JOIN (
#             SELECT 
#                 customer_name, 
#                 COUNT(name) AS total_deals,
#                 SUM(CASE WHEN warranty_amc_status IN ('IN Warranty', 'AMC Active') THEN 1 ELSE 0 END) AS active_deals
#             FROM `tabCRM Deal`
#             GROUP BY customer_name
#         ) d ON d.customer_name = c.name

#         LEFT JOIN (
#             SELECT 
#                 customer, 
#                 COUNT(name) AS total_quotes,
#                 SUM(CASE WHEN status = 'Quote Won' THEN 1 ELSE 0 END) AS quotes_won
#             FROM `tabCRM Quotation`
#             GROUP BY customer
#         ) q ON q.customer = c.name

#         LEFT JOIN (
#             SELECT 
#                 customer,
#                 COUNT(name) AS total_contracts,
#                 SUM(CASE WHEN expiry_date > CURDATE() THEN 1 ELSE 0 END) AS active_contracts,
#                 MIN(start_date) AS start_date
#             FROM `tabCRM Contract`
#             WHERE docstatus = 1
#             GROUP BY customer
#         ) ct ON ct.customer = c.name

#         WHERE 1=1 {conditions}
#     """, filters, as_dict=True)


import frappe

def execute(filters=None):
    conditions = ""

    if filters.get("customer"):
        conditions += " AND c.name = %(customer)s"

    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND ct.start_date BETWEEN %(from_date)s AND %(to_date)s"

    columns = get_columns()
    data = get_data(filters, conditions)
    chart = get_chart(data)

    return columns, data, None, chart


def get_columns():
    return [
        {"label": "<b>Customer HC</b>", "fieldname": "customer_hc", "fieldtype": "Data", "width": 120},
        {"label": "<b>Customer Name</b>", "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
        {"label": "<b>Total Projects</b>", "fieldname": "total_projects", "fieldtype": "Int", "width": 120},
        {"label": "<b>Active Projects</b>", "fieldname": "active_projects", "fieldtype": "Int", "width": 140},
        {"label": "<b>Total Deals</b>", "fieldname": "total_deals", "fieldtype": "Int", "width": 100},
        {"label": "<b>Active Deals</b>", "fieldname": "active_deals", "fieldtype": "Int", "width": 130},
        {"label": "<b>Warranty Conversion</b>", "fieldname": "warranty_conversion", "fieldtype": "Int", "width": 180},
        {"label": "<b>AMC Renewals</b>", "fieldname": "amc_renewal", "fieldtype": "Int", "width": 180},
        {"label": "<b>Lost AMC Conversions</b>", "fieldname": "lost_amc_conversion", "fieldtype": "Int", "width": 180},
        {"label": "<b>Lost Warranty Conversions</b>", "fieldname": "lost_Warranty_conversion", "fieldtype": "Int", "width": 180},
        {"label": "<b>Total Quotes</b>", "fieldname": "total_quotes", "fieldtype": "Int", "width": 130},
        {"label": "<b>Quotes Won</b>", "fieldname": "quotes_won", "fieldtype": "Int", "width": 130},
        {"label": "<b>Total Contracts</b>", "fieldname": "total_contracts", "fieldtype": "Int", "width": 150},
        {"label": "<b>Active Contracts</b>", "fieldname": "active_contracts", "fieldtype": "Int", "width": 150},
    ]


def get_data(filters, conditions):
    return frappe.db.sql(f"""
        SELECT 
            c.name AS customer_hc,
            c.organization_name AS customer_name,
            IFNULL(p.total_projects, 0) AS total_projects,
            IFNULL(p.active_projects, 0) AS active_projects,
            IFNULL(d.total_deals, 0) AS total_deals,
            IFNULL(d.active_deals, 0) AS active_deals,
            IFNULL(wc.active_wc_deals,0) AS warranty_conversion,
            IFNULL(amc.active_amc_deals,0) As amc_renewal,
            IFNULL(lwc.active_lwc_deals,0) As lost_Warranty_conversion,
            IFNULL(lac.active_lac_deals,0) As lost_amc_conversion,
            IFNULL(q.total_quotes, 0) AS total_quotes,
            IFNULL(q.quotes_won, 0) AS quotes_won,
            IFNULL(ct.total_contracts, 0) AS total_contracts,
            IFNULL(ct.active_contracts, 0) AS active_contracts

        FROM `tabCRM Organization` c

        LEFT JOIN (
            SELECT 
                customer, 
                COUNT(name) AS total_projects,
                SUM(CASE WHEN status IN ('IN Warranty', 'AMC Active') THEN 1 ELSE 0 END) AS active_projects
            FROM `tabProject`
            GROUP BY customer
        ) p ON p.customer = c.name

        LEFT JOIN (
            SELECT 
                customer_name,
                customer, 
                COUNT(name) AS total_deals,
                SUM(CASE WHEN warranty_amc_status IN ('IN Warranty', 'AMC Active') THEN 1 ELSE 0 END) AS active_deals
            FROM `tabCRM Deal`
            GROUP BY customer_name
        ) d ON d.customer = c.name
                         
        LEFT JOIN (
            SELECT 
                customer_name, 
                         customer,
                COUNT(name) AS total_deals,
                SUM(CASE WHEN warranty_amc_status IN ('IN Warranty', 'AMC Active') THEN 1 ELSE 0 END) AS active_wc_deals
            FROM `tabCRM Deal`
            WHERE deal_type="Warranty Conversion"
            GROUP BY customer_name) wc ON wc.customer = c.name

        LEFT JOIN (
            SELECT 
                customer_name, 
                COUNT(name) AS total_deals,
                customer,
                SUM(CASE WHEN warranty_amc_status IN ('IN Warranty', 'AMC Active') THEN 1 ELSE 0 END) AS active_amc_deals
            FROM `tabCRM Deal`
            WHERE deal_type="AMC Renewal"
            GROUP BY customer_name
        ) amc ON amc.customer = c.name

        LEFT JOIN (
            SELECT 
                customer_name, 
                COUNT(name) AS total_deals,
customer,
                SUM(CASE WHEN warranty_amc_status IN ('IN Warranty', 'AMC Active') THEN 1 ELSE 0 END) AS active_lwc_deals
            FROM `tabCRM Deal`
            WHERE deal_type="Lost Warranty Conversion"
            GROUP BY customer_name
        ) lwc ON lwc.customer = c.name

        LEFT JOIN (
            SELECT 
                customer_name, 
                customer,
                COUNT(name) AS total_deals,
                SUM(CASE WHEN warranty_amc_status IN ('IN Warranty', 'AMC Active') THEN 1 ELSE 0 END) AS active_lac_deals
            FROM `tabCRM Deal`
            WHERE deal_type="Lost AMC Conversion"
            GROUP BY customer_name
        ) lac ON lac.customer = c.name


        LEFT JOIN (
            SELECT 
                customer, 
                COUNT(name) AS total_quotes,
                SUM(CASE WHEN status = 'Quote Won' THEN 1 ELSE 0 END) AS quotes_won
            FROM `tabCRM Quotation`
            GROUP BY customer
        ) q ON q.customer = c.name

        LEFT JOIN (
            SELECT 
                customer,
                COUNT(name) AS total_contracts,
                SUM(CASE WHEN expiry_date > CURDATE() THEN 1 ELSE 0 END) AS active_contracts,
                MIN(start_date) AS start_date
            FROM `tabCRM Contract`
            WHERE docstatus = 1
            GROUP BY customer
        ) ct ON ct.customer = c.name

        WHERE 1=1 {conditions}
    """, filters, as_dict=True)


def get_chart(data):
    # Aggregate total and active counts
    total_projects = sum(row["total_projects"] for row in data)
    active_projects = sum(row["active_projects"] for row in data)

    total_deals = sum(row["total_deals"] for row in data)
    active_deals = sum(row["active_deals"] for row in data)

    total_quotes = sum(row["total_quotes"] for row in data)
    quotes_won = sum(row["quotes_won"] for row in data)

    total_contracts = sum(row["total_contracts"] for row in data)
    active_contracts = sum(row["active_contracts"] for row in data)

    # Avoid division by zero
    def get_percentage(part, whole):
        return round((part / whole) * 100, 2) if whole > 0 else 0

    labels = ["Projects", "Deals", "Quotes", "Contracts"]

    percent_active = [
        get_percentage(active_projects, total_projects),
        get_percentage(active_deals, total_deals),
        get_percentage(quotes_won, total_quotes),
        get_percentage(active_contracts, total_contracts),
    ]

    percent_inactive = [100 - val for val in percent_active]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": f"Inactive/Lost %",
                    "values": percent_inactive
                },
                {
                    "name": f"Active/Won %",
                    "values": percent_active
                }
            ]
        },
        "type": "bar",
        "barOptions": {
            "stacked": True
        },
         "colors": ["#C741E2", "#eede53"]
        #  "axisOptions": {
        #     "yAxisMode": "tick",
        #     "xAxisMode": "tick",
        #     "xIsSeries": True
        # }
		# ,
        # "tooltipOptions": {
        #     "formatTooltipY": lambda val: f"{val}%"
        # }
    }
