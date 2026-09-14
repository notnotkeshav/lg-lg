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
    # CONTRACT CONDITIONS
    #
    # The ASM is the `user` link on the contract - never the
    # `asm_name` text, which is only a fetched copy of the user's
    # full name and does not always match a User record.
    # -------------------------------------------------------------

    def contract_conditions(alias):
        conditions = [
            f"{alias}.docstatus < 2",

            # Customer PO Date is mandatory for this report
            f"{alias}.customer_po_date IS NOT NULL",

            # Selected year is based on Customer PO Date
            f"YEAR({alias}.customer_po_date) = %(year)s",
        ]

        if filters.get("deal_type"):
            conditions.append(
                f"{alias}.deal_type = %(deal_type)s"
            )

        if filters.get("asm"):
            conditions.append(
                f"{alias}.user = %(asm)s"
            )

        if filters.get("region"):
            conditions.append(
                f"{alias}.region = %(region)s"
            )

        if filters.get("branch"):
            conditions.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM `tabRegion Branches` fb
                    WHERE fb.name = {alias}.branch
                      AND (
                            fb.name = %(branch)s
                            OR fb.branch_code = %(branch)s
                            OR fb.branch_name = %(branch)s
                      )
                )
                """
            )

        return " AND ".join(conditions)

    contract_where = contract_conditions("c")

    # -------------------------------------------------------------
    # USER / ASM CONDITIONS
    # -------------------------------------------------------------

    user_conditions = [
        "u.enabled = 1",

        "u.name NOT IN ('Administrator', 'Guest')",

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
    # ASM / REGION / BRANCH DIMENSION
    #
    # Region and Branch are taken from the contract itself, so an
    # ASM working across branches gets one row per branch and the
    # columns are never empty for a row that has contracts.
    #
    # Area Managers without a single contract in the selected year
    # are added with no Region / Branch so they still show up as
    # zero rows - skipped when a Region / Branch filter is on,
    # since they cannot satisfy it.
    # -------------------------------------------------------------

    asm_dimension_sql = f"""
        SELECT
            c.user AS asm_user,
            c.region AS region,
            c.branch AS branch
        FROM `tabCRM Contract` c
        WHERE {contract_where}
        GROUP BY
            c.user,
            c.region,
            c.branch
    """

    if not (filters.get("region") or filters.get("branch")):
        asm_dimension_sql += f"""
            UNION

            SELECT
                u.name,
                NULL,
                NULL
            FROM `tabUser` u
            WHERE {user_where}
              AND NOT EXISTS (
                    SELECT 1
                    FROM `tabCRM Contract` c2
                    WHERE c2.user = u.name
                      AND {contract_conditions("c2")}
              )
        """

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

            COALESCE(
                NULLIF(du.full_name, ''),
                NULLIF(asm.asm_user, ''),
                'Unassigned'
            ) AS asm_name,

            COALESCE(db.region, asm.region) AS region,

            COALESCE(db.branch_name, asm.branch) AS branch,

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

        LEFT JOIN `tabUser` du
            ON du.name = asm.asm_user

        LEFT JOIN `tabRegion Branches` db
            ON db.name = asm.branch

        CROSS JOIN (
            {periods_sql}
        ) periods

        LEFT JOIN `tabCRM Contract` c
            ON c.user <=> asm.asm_user
            AND c.region <=> asm.region
            AND c.branch <=> asm.branch
            AND {contract_where}
            AND {period_match}

        GROUP BY
            asm.asm_user,
            asm.region,
            asm.branch,
            du.full_name,
            db.region,
            db.branch_name,
            periods.period_no

        ORDER BY
            region,
            branch,
            asm_name,
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
