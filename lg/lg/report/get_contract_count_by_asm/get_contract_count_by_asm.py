import frappe
from frappe import _


DEAL_TYPES = [
    "AMC Renewal",
    "Warranty AMC Conversion",
    "Lost Warranty Conversion",
    "Lost AMC Conversion",
]


def execute(filters=None):
    filters = frappe._dict(filters or {})

    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters):
    group_by = filters.get("group_by", "Monthly")

    if group_by == "Monthly":
        period_label = _("Month")
    elif group_by == "Quarterly":
        period_label = _("Quarter")
    elif group_by == "Annually":
        period_label = _("Year")
    else:
        frappe.throw(_("Invalid Group By option"))

    return [
        {
            "label": _("ASM Name"),
            "fieldname": "asm_name",
            "fieldtype": "Data",
            "width": 200,
        },
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
            "label": period_label,
            "fieldname": "period",
            "fieldtype": "Data",
            "width": 120,
        },

        # ---------------------------------------------------------
        # REVENUE COLUMNS
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # COUNT COLUMNS
        # ---------------------------------------------------------

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
    year = filters.get("year")

    if not year:
        year = frappe.utils.getdate().year

    try:
        year = int(year)
    except (TypeError, ValueError):
        frappe.throw(_("Invalid year"))

    group_by = filters.get("group_by", "Monthly")

    # -------------------------------------------------------------
    # PERIODS
    # -------------------------------------------------------------

    if group_by == "Monthly":

        period_sql = """
            MONTHNAME(
                MAKEDATE(%(year)s, 1)
                + INTERVAL periods.period_no - 1 MONTH
            )
        """

        period_order_sql = "periods.period_no"

        periods_sql = """
            SELECT 1 AS period_no
            UNION ALL SELECT 2
            UNION ALL SELECT 3
            UNION ALL SELECT 4
            UNION ALL SELECT 5
            UNION ALL SELECT 6
            UNION ALL SELECT 7
            UNION ALL SELECT 8
            UNION ALL SELECT 9
            UNION ALL SELECT 10
            UNION ALL SELECT 11
            UNION ALL SELECT 12
        """

    elif group_by == "Quarterly":

        period_sql = """
            CONCAT('Q', periods.period_no)
        """

        period_order_sql = "periods.period_no"

        periods_sql = """
            SELECT 1 AS period_no
            UNION ALL SELECT 2
            UNION ALL SELECT 3
            UNION ALL SELECT 4
        """

    elif group_by == "Annually":

        period_sql = """
            CAST(%(year)s AS CHAR)
        """

        period_order_sql = "periods.period_no"

        periods_sql = """
            SELECT 1 AS period_no
        """

    else:
        frappe.throw(_("Invalid Group By option"))

    # -------------------------------------------------------------
    # USER / ASM CONDITIONS
    #
    # The ASM dimension is built from Users only - never from
    # `tabRegion Branches`. A branch head heading more than one
    # branch would otherwise repeat every one of their contracts
    # once per branch.
    # -------------------------------------------------------------

    user_conditions = [
        "u.enabled = 1",

        """
        EXISTS (
            SELECT 1
            FROM `tabHas Role` hr
            WHERE hr.parent = u.name
              AND hr.role = 'Area Manager'
        )
        """
    ]

    if filters.get("asm"):
        user_conditions.append(
            "u.name = %(asm)s"
        )

    user_where = " AND ".join(user_conditions)

    # -------------------------------------------------------------
    # CONTRACT CONDITIONS
    # -------------------------------------------------------------

    contract_conditions = [
        "c.docstatus < 2",

        # Customer PO Date is mandatory for this report
        "c.customer_po_date IS NOT NULL",

        # Selected year is based on Customer PO Date
        "YEAR(c.customer_po_date) = %(year)s",
    ]

    if filters.get("deal_type"):
        contract_conditions.append(
            "c.deal_type = %(deal_type)s"
        )

    contract_where = " AND ".join(contract_conditions)

    # -------------------------------------------------------------
    # ASM DIMENSION
    #
    # Area Managers, plus any ASM name found on a contract of the
    # selected year that matches no Area Manager User - those
    # contracts are reported under their own name instead of being
    # dropped silently.
    # -------------------------------------------------------------

    asm_dimension_sql = f"""
        SELECT u.full_name AS asm_name
        FROM `tabUser` u
        WHERE {user_where}
          AND IFNULL(u.full_name, '') <> ''
    """

    if not filters.get("asm"):
        asm_dimension_sql += f"""
            UNION

            SELECT DISTINCT c.asm_name
            FROM `tabCRM Contract` c
            WHERE {contract_where}
              AND IFNULL(c.asm_name, '') <> ''
              AND NOT EXISTS (
                    SELECT 1
                    FROM `tabUser` u2
                    WHERE u2.full_name = c.asm_name
                      AND u2.enabled = 1
                      AND EXISTS (
                            SELECT 1
                            FROM `tabHas Role` hr2
                            WHERE hr2.parent = u2.name
                              AND hr2.role = 'Area Manager'
                      )
              )
        """

    # -------------------------------------------------------------
    # REGION / BRANCH
    #
    # Pre-aggregated per ASM, so an ASM heading several branches
    # stays a single row and their branches are listed together.
    # -------------------------------------------------------------

    asm_branch_map_sql = """
        SELECT
            u.full_name AS asm_name,

            GROUP_CONCAT(
                DISTINCT b.region
                ORDER BY b.region
                SEPARATOR ', '
            ) AS region,

            GROUP_CONCAT(
                DISTINCT b.branch_name
                ORDER BY b.branch_name
                SEPARATOR ', '
            ) AS branch

        FROM `tabRegion Branches` b

        INNER JOIN `tabUser` u
            ON b.branch_head = u.name

        GROUP BY u.full_name
    """

    # Region / Branch filters match any branch the ASM heads.

    dimension_conditions = [
        "1 = 1"
    ]

    if filters.get("region"):
        dimension_conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM `tabRegion Branches` b2
                INNER JOIN `tabUser` u3
                    ON b2.branch_head = u3.name
                WHERE u3.full_name = asm.asm_name
                  AND b2.region = %(region)s
            )
            """
        )

    if filters.get("branch"):
        dimension_conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM `tabRegion Branches` b3
                INNER JOIN `tabUser` u4
                    ON b3.branch_head = u4.name
                WHERE u4.full_name = asm.asm_name
                  AND (
                        b3.name = %(branch)s
                        OR b3.branch_code = %(branch)s
                        OR b3.branch_name = %(branch)s
                  )
            )
            """
        )

    dimension_where = " AND ".join(dimension_conditions)

    # -------------------------------------------------------------
    # PERIOD MATCH
    # -------------------------------------------------------------

    if group_by == "Monthly":

        period_match = """
            MONTH(c.customer_po_date) = periods.period_no
        """

    elif group_by == "Quarterly":

        period_match = """
            QUARTER(c.customer_po_date) = periods.period_no
        """

    elif group_by == "Annually":

        period_match = """
            YEAR(c.customer_po_date) = %(year)s
        """

    else:
        frappe.throw(_("Invalid Group By option"))

    # -------------------------------------------------------------
    # MAIN QUERY
    # -------------------------------------------------------------

    query = f"""
        SELECT

            asm.asm_name AS asm_name,

            map.region AS region,

            map.branch AS branch,

            {period_sql} AS period,

            # =====================================================
            # REVENUE
            # =====================================================

            COALESCE(
                SUM(
                    CASE
                        WHEN c.deal_type = 'AMC Renewal'
                        THEN COALESCE(c.amount, 0)
                        ELSE 0
                    END
                ),
                0
            ) AS amc_renewal_amount,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.deal_type = 'Warranty AMC Conversion'
                        THEN COALESCE(c.amount, 0)
                        ELSE 0
                    END
                ),
                0
            ) AS warranty_amc_conversion_amount,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.deal_type = 'Lost Warranty Conversion'
                        THEN COALESCE(c.amount, 0)
                        ELSE 0
                    END
                ),
                0
            ) AS lost_warranty_conversion_amount,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.deal_type = 'Lost AMC Conversion'
                        THEN COALESCE(c.amount, 0)
                        ELSE 0
                    END
                ),
                0
            ) AS lost_amc_conversion_amount,

            COALESCE(SUM(COALESCE(c.amount, 0)), 0) AS total_amount,

            # =====================================================
            # COUNTS
            # =====================================================

            COALESCE(
                SUM(
                    CASE
                        WHEN c.deal_type = 'AMC Renewal'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS amc_renewal,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.deal_type = 'Warranty AMC Conversion'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS warranty_amc_conversion,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.deal_type = 'Lost Warranty Conversion'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS lost_warranty_conversion,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.deal_type = 'Lost AMC Conversion'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS lost_amc_conversion,

            COUNT(c.name) AS total

        FROM (
            {asm_dimension_sql}
        ) asm

        LEFT JOIN (
            {asm_branch_map_sql}
        ) map
            ON map.asm_name = asm.asm_name

        CROSS JOIN (
            {periods_sql}
        ) periods

        LEFT JOIN `tabCRM Contract` c
            ON c.asm_name = asm.asm_name
            AND {contract_where}
            AND {period_match}

        WHERE
            {dimension_where}

        GROUP BY
            asm.asm_name,
            map.region,
            map.branch,
            periods.period_no

        ORDER BY
            map.region,
            map.branch,
            asm.asm_name,
            {period_order_sql}
    """

    return frappe.db.sql(
        query,
        {
            "year": year,
            "asm": filters.get("asm"),
            "region": filters.get("region"),
            "branch": filters.get("branch"),
            "deal_type": filters.get("deal_type"),
        },
        as_dict=True,
    )
