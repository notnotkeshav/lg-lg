import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}

    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters):
    group_by = filters.get("group_by", "Monthly")

    if group_by == "Monthly":
        period_label = _("Month")

    elif group_by == "Quarterly":
        period_label = _("Quarter")

    else:
        period_label = _("Year")

    return [
        # =========================================================
        # BASIC INFORMATION
        # =========================================================

        {
            "label": _("Region"),
            "fieldname": "region",
            "fieldtype": "Data",
            "width": 150,
        },

        {
            "label": _("Branch"),
            "fieldname": "branch",
            "fieldtype": "Data",
            "width": 150,
        },

        {
            "label": _("ASM Name"),
            "fieldname": "asm_name",
            "fieldtype": "Data",
            "width": 200,
        },

        {
            "label": period_label,
            "fieldname": "period",
            "fieldtype": "Data",
            "width": 120,
        },

        # =========================================================
        # REVENUE / AMOUNT COLUMNS
        # =========================================================

        {
            "label": _("AMC Renewal Revenue"),
            "fieldname": "amc_renewal_amount",
            "fieldtype": "Currency",
            "width": 170,
        },

        {
            "label": _("Warranty AMC Conversion Revenue"),
            "fieldname": "warranty_amc_conversion_amount",
            "fieldtype": "Currency",
            "width": 220,
        },

        {
            "label": _("Lost Warranty Conversion Revenue"),
            "fieldname": "lost_warranty_conversion_amount",
            "fieldtype": "Currency",
            "width": 210,
        },

        {
            "label": _("Lost AMC Conversion Revenue"),
            "fieldname": "lost_amc_conversion_amount",
            "fieldtype": "Currency",
            "width": 190,
        },

        {
            "label": _("Total Revenue"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 150,
        },

        # =========================================================
        # COUNT COLUMNS
        # =========================================================

        {
            "label": _("AMC Renewal Count"),
            "fieldname": "amc_renewal",
            "fieldtype": "Int",
            "width": 140,
        },

        {
            "label": _("Warranty AMC Conversion Count"),
            "fieldname": "warranty_amc_conversion",
            "fieldtype": "Int",
            "width": 210,
        },

        {
            "label": _("Lost Warranty Conversion Count"),
            "fieldname": "lost_warranty_conversion",
            "fieldtype": "Int",
            "width": 200,
        },

        {
            "label": _("Lost AMC Conversion Count"),
            "fieldname": "lost_amc_conversion",
            "fieldtype": "Int",
            "width": 180,
        },

        {
            "label": _("Total Count"),
            "fieldname": "total",
            "fieldtype": "Int",
            "width": 110,
        },
    ]


def get_data(filters):
    conditions = [
        "docstatus < 2"
    ]

    # =========================================================
    # REGION FILTER
    # =========================================================

    if filters.get("region"):
        conditions.append(
            "region = {}".format(
                frappe.db.escape(filters.get("region"))
            )
        )

    # =========================================================
    # BRANCH FILTER
    # =========================================================

    if filters.get("branch"):
        conditions.append(
            "branch = {}".format(
                frappe.db.escape(filters.get("branch"))
            )
        )

    # =========================================================
    # ASM FILTER
    # =========================================================

    if filters.get("asm"):
        full_name = frappe.db.get_value(
            "User",
            filters.get("asm"),
            "full_name"
        )

        if full_name:
            conditions.append(
                "asm_name = {}".format(
                    frappe.db.escape(full_name)
                )
            )
        else:
            conditions.append(
                "asm_name = {}".format(
                    frappe.db.escape(filters.get("asm"))
                )
            )

    # =========================================================
    # YEAR FILTER
    # =========================================================

    if filters.get("year"):
        conditions.append(
            "YEAR(creation) = {}".format(
                frappe.db.escape(filters.get("year"))
            )
        )

    # =========================================================
    # DEAL TYPE FILTER
    # =========================================================

    if filters.get("deal_type"):
        conditions.append(
            "deal_type = {}".format(
                frappe.db.escape(filters.get("deal_type"))
            )
        )

    # =========================================================
    # PERIOD GROUPING
    # =========================================================

    group_by = filters.get("group_by", "Monthly")

    if group_by == "Monthly":

        # Example:
        # January
        # February
        # March

        period_sql = """
            MONTHNAME(creation)
        """

        # Keep months in chronological order
        period_order_sql = """
            MONTH(creation)
        """

    elif group_by == "Quarterly":

        # Example:
        # Q1
        # Q2
        # Q3
        # Q4

        period_sql = """
            CONCAT(
                'Q',
                QUARTER(creation)
            )
        """

        period_order_sql = """
            QUARTER(creation)
        """

    elif group_by == "Annually":

        # Example:
        # 2024
        # 2025
        # 2026

        period_sql = """
            CAST(YEAR(creation) AS CHAR)
        """

        period_order_sql = """
            YEAR(creation)
        """

    else:
        frappe.throw(_("Invalid Group By option"))

    where_clause = " AND ".join(conditions)

    # =========================================================
    # QUERY
    # =========================================================

    query = f"""
        SELECT

            region,

            branch,

            asm_name,

            {period_sql} AS period,

            # =================================================
            # REVENUE / AMOUNT
            # =================================================

            SUM(
                CASE
                    WHEN deal_type = 'AMC Renewal'
                    THEN COALESCE(amount, 0)
                    ELSE 0
                END
            ) AS amc_renewal_amount,

            SUM(
                CASE
                    WHEN deal_type = 'Warranty AMC Conversion'
                    THEN COALESCE(amount, 0)
                    ELSE 0
                END
            ) AS warranty_amc_conversion_amount,

            SUM(
                CASE
                    WHEN deal_type = 'Lost Warranty Conversion'
                    THEN COALESCE(amount, 0)
                    ELSE 0
                END
            ) AS lost_warranty_conversion_amount,

            SUM(
                CASE
                    WHEN deal_type = 'Lost AMC Conversion'
                    THEN COALESCE(amount, 0)
                    ELSE 0
                END
            ) AS lost_amc_conversion_amount,

            SUM(
                COALESCE(amount, 0)
            ) AS total_amount,

            # =================================================
            # COUNTS
            # =================================================

            SUM(
                CASE
                    WHEN deal_type = 'AMC Renewal'
                    THEN 1
                    ELSE 0
                END
            ) AS amc_renewal,

            SUM(
                CASE
                    WHEN deal_type = 'Warranty AMC Conversion'
                    THEN 1
                    ELSE 0
                END
            ) AS warranty_amc_conversion,

            SUM(
                CASE
                    WHEN deal_type = 'Lost Warranty Conversion'
                    THEN 1
                    ELSE 0
                END
            ) AS lost_warranty_conversion,

            SUM(
                CASE
                    WHEN deal_type = 'Lost AMC Conversion'
                    THEN 1
                    ELSE 0
                END
            ) AS lost_amc_conversion,

            COUNT(name) AS total

        FROM `tabCRM Contract`

        WHERE {where_clause}

        # =====================================================
        # ONE ROW PER REGION + BRANCH + ASM + PERIOD
        # =====================================================

        GROUP BY
            region,
            branch,
            asm_name,
            {period_sql}

        ORDER BY
            region,
            branch,
            asm_name,
            {period_order_sql}
    """

    return frappe.db.sql(
        query,
        as_dict=True
    )