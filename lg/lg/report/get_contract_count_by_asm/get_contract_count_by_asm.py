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
        {
            "label": _("AMC Renewal"),
            "fieldname": "amc_renewal",
            "fieldtype": "Int",
            "width": 130,
        },
        {
            "label": _("Warranty AMC Conversion"),
            "fieldname": "warranty_amc_conversion",
            "fieldtype": "Int",
            "width": 180,
        },
        {
            "label": _("Lost Warranty Conversion"),
            "fieldname": "lost_warranty_conversion",
            "fieldtype": "Int",
            "width": 180,
        },
        {
            "label": _("Lost AMC Conversion"),
            "fieldname": "lost_amc_conversion",
            "fieldtype": "Int",
            "width": 160,
        },
        {
            "label": _("Total"),
            "fieldname": "total",
            "fieldtype": "Int",
            "width": 100,
        },
    ]


def get_data(filters):
    conditions = ["docstatus < 2"]

    # Region filter
    if filters.get("region"):
        conditions.append("region = {}".format(frappe.db.escape(filters.get("region"))))

    # Branch filter
    if filters.get("branch"):
        conditions.append("branch = {}".format(frappe.db.escape(filters.get("branch"))))

    # ASM filter
    if filters.get("asm"):
        full_name = frappe.db.get_value("User", filters.get("asm"), "full_name")

        if full_name:
            conditions.append("asm_name = {}".format(frappe.db.escape(full_name)))
        else:
            conditions.append(
                "asm_name = {}".format(frappe.db.escape(filters.get("asm")))
            )

    # Year filter
    if filters.get("year"):
        conditions.append(
            "YEAR(creation) = {}".format(frappe.db.escape(filters.get("year")))
        )

    # Contract Type filter
    if filters.get("deal_type"):
        conditions.append(
            "deal_type = {}".format(frappe.db.escape(filters.get("deal_type")))
        )

    group_by = filters.get("group_by", "Monthly")

    # Period
    if group_by == "Monthly":
        period_sql = """
            CONCAT(
                YEAR(creation),
                '-',
                LPAD(MONTH(creation), 2, '0')
            )
        """

        period_order_sql = """
            YEAR(creation),
            MONTH(creation)
        """

    elif group_by == "Quarterly":
        period_sql = """
            CONCAT(
                YEAR(creation),
                '-Q',
                QUARTER(creation)
            )
        """

        period_order_sql = """
            YEAR(creation),
            QUARTER(creation)
        """

    elif group_by == "Annually":
        period_sql = """
            CAST(YEAR(creation) AS CHAR)
        """

        period_order_sql = """
            YEAR(creation)
        """

    else:
        frappe.throw(_("Invalid Group By option"))

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT
            region,
            branch,
            asm_name,

            {period_sql} AS period,

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

    return frappe.db.sql(query, as_dict=True)
