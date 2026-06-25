# opportunity_hp_summary.py
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate

def execute(filters=None):
    """
    Opportunity HP Summary (Frappe methods only, no raw SQL)
    - Aggregates hp from child table "Product Details" for Opportunity
    - Group by Project (IL), Branch, AM, Region, or RSM
    - Default Opportunity Category = 'Sales'
    """

    filters = filters or {}
    # defaults (user-seen label should be Opportunity Category)
    filters.setdefault("opportunity_category", "Sales")
    filters.setdefault("group_by", "Project")
    filters.setdefault("from_date", "2000-01-01")
    filters.setdefault("to_date", nowdate())
    filters.setdefault("chart_type", "bar")
    filters.setdefault("bar_chart_wise", "HP")

    # Allowed group_by values
    group_by = filters.get("group_by")
    allowed_groups = ("Project", "Branch", "AM", "Region", "RSM")
    if group_by not in allowed_groups:
        group_by = "Project"

    # Build base filters for Opportunities (we'll further filter AM in Python)
    opp_filters = {
        "docstatus": ["<", 2]
    }
    # deal_category is internal field for what you call Opportunity Category
    if filters.get("opportunity_category"):
        opp_filters["deal_category"] = filters.get("opportunity_category")

    # date range on register_date
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    if from_date and to_date:
        opp_filters["register_date"] = ["between", [from_date, to_date]]
    elif from_date:
        opp_filters["register_date"] = [">=", from_date]
    elif to_date:
        opp_filters["register_date"] = ["<=", to_date]

    # quick exact filters for project/branch/region (these are simple)
    if filters.get("project"):
        opp_filters["project"] = filters.get("project")
    if filters.get("branch"):
        opp_filters["branch"] = filters.get("branch")
    if filters.get("region"):
        opp_filters["region"] = filters.get("region")

    # fetch opportunities (fields we need)
    # NOTE: limit_page_length=0 returns ALL rows in many Frappe versions; if your install doesn't allow 0,
    # change to a high number or paginate in production.
    opps = frappe.get_all(
        "CRM Deal",
        filters=opp_filters,
        fields=["name", "project", "branch", "region", "branch.branch_head_name", "owner", "warranty_amc_status"],
        limit_page_length=0
    ) or []

    # if AM filter is provided we will filter results in Python (because AM can come from Branch or Opportunity owner)
    am_filter = filters.get("am")

    # collect referenced branches/regions to fetch branch_head_name and region_head_name
    branch_names = list({o.get("branch") for o in opps if o.get("branch")})
    region_names = list({o.get("region") for o in opps if o.get("region")})

    branches = {}
    if branch_names:
        b_rows = frappe.get_all("Region Branches",
            filters={"name": ["in", branch_names]},
            fields=["name", "branch_head_name"], limit_page_length=0) or []
        branches = {b["name"]: b for b in b_rows}

    regions = {}
    if region_names:
        r_rows = frappe.get_all("Region Master",
            filters={"name": ["in", region_names]},
            fields=["name", "region_head_name"], limit_page_length=0) or []
        regions = {r["name"]: r for r in r_rows}

    # get Product Details rows for these opportunities
    opp_names = [o["name"] for o in opps]
    pd_rows = []
    if opp_names:
        pd_rows = frappe.get_all("Product Details",
            filters={"parent": ["in", opp_names]},
            fields=["parent", "hp", "tonnes"],
            limit_page_length=0) or []

    # aggregate hp per opportunity (parent)
    hp_by_opp = {}
    tonne_by_opp = {}
    count_by_opp = {}
    for pd in pd_rows:
        parent = pd.get("parent")
        hp_val = pd.get("hp") or 0
        tonne_val = pd.get("tonnes") or 0
        try:
            hp_val = float(hp_val)
            tonne_val = float(tonne_val)
        except Exception:
            hp_val = 0.0
            tonne_val = 0.0
        hp_by_opp[parent] = hp_by_opp.get(parent, 0.0) + hp_val
        tonne_by_opp[parent] = tonne_by_opp.get(parent, 0.0) + tonne_val
        count_by_opp[parent] = count_by_opp.get(parent, 0) + 1

    # Build group value per opportunity and aggregate totals per group
    group_totals = {}       # group_value -> total_hp
    group_totals_tonne = {}       # group_value -> total_tonne
    group_status_total = {}       # group_value -> product_count
    group_status_total_hp = {}       # group_value -> product_count
    group_status_total_tonne = {}       # group_value -> product_count
    group_counts = {}       # group_value -> product_count
    opps_included = 0

    for o in opps:
        name = o.get("name")
        # apply AM filter (if requested). AM may be branch_head_name, account_manager or owner
        branch_head = None
        if o.get("branch") and branches.get(o.get("branch")):
            branch_head = branches[o.get("branch")].get("branch_head_name")

        region_head = None
        if o.get("region") and regions.get(o.get("region")):
            region_head = regions[o.get("region")].get("region_head_name")

        # candidate AM values
        candidate_am = branch_head or o.get("account_manager") or o.get("owner")
        # if am filter present, skip opp if not matching any of the AM identifiers
        if am_filter:
            matches_am = False
            if branch_head and branch_head == am_filter:
                matches_am = True
            if o.get("account_manager") and o.get("account_manager") == am_filter:
                matches_am = True
            if o.get("owner") and o.get("owner") == am_filter:
                matches_am = True
            if not matches_am:
                continue

        # decide group_value based on group_by
        if group_by == "Project":
            group_value = o.get("project") or _("(No Project)")
        elif group_by == "Branch":
            group_value = o.get("branch") or _("(No Branch)")
        elif group_by == "AM":
            # prefer branch head, then account_manager, then owner
            group_value = branch_head or o.get("account_manager") or o.get("owner") or _("(No AM)")
        elif group_by == "Region":
            group_value = o.get("region") or _("(No Region)")
        elif group_by == "RSM":
            group_value = region_head or o.get("region") or _("(No RSM)")
        else:
            group_value = _("(Other)")

        opp_hp = hp_by_opp.get(name, 0.0)
        opp_tonne = tonne_by_opp.get(name, 0.0)
        opp_count = count_by_opp.get(name, 0)

        group_totals[group_value] = group_totals.get(group_value, 0.0) + opp_hp
        group_totals_tonne[group_value] = group_totals_tonne.get(group_value, 0.0) + opp_tonne
        group_counts[group_value] = group_counts.get(group_value, 0) + opp_count
        
        status_total = group_status_total.get(group_value, {})
        opp_status = o.get("warranty_amc_status", "IN Warranty") or "IN Warranty"
        status_total[opp_status] = status_total.get(opp_status, 0.0) + (opp_hp if filters.get("bar_chart_wise", "HP") == "HP" else opp_tonne)
        group_status_total[group_value] = status_total
        
        status_total_hp = group_status_total_hp.get(group_value, {})
        status_total_tonne = group_status_total_tonne.get(group_value, {})
        opp_status = o.get("warranty_amc_status", "IN Warranty") or "IN Warranty"
        status_total_hp[opp_status] = status_total_hp.get(opp_status, 0.0) + opp_hp
        status_total_tonne[opp_status] = status_total_tonne.get(opp_status, 0.0) + opp_tonne
        group_status_total_hp[group_value] = status_total_hp
        group_status_total_tonne[group_value] = status_total_tonne
        
        opps_included += 1

    # convert aggregated dicts into sorted rows
    frappe.errprint("HP")
    frappe.errprint(group_status_total_hp)
    frappe.errprint("Tonne")
    frappe.errprint(group_status_total_tonne)
    sorted_groups = sorted(group_totals.items(), key=lambda x: x[1], reverse=True)
    data = []
    grand_total_hp = 0.0
    grand_total_tonnes = 0.0
    for gv, total in sorted_groups:
        count = group_counts.get(gv, 0)
        tonnes = group_totals_tonne.get(gv, 0)
        grand_total_hp += total
        grand_total_tonnes += tonnes
        formatted_hp = "{:,.0f}".format(total)
        formatted_tonne = "{:,.0f}".format(tonnes)
        # simple HTML for nicer first column
        badge_label = {
            "Project": _("IL"),
            "Branch": _("Branch"),
            "AM": _("AM"),
            "Region": _("Region"),
            "RSM": _("RSM")
        }.get(group_by, group_by)

        group_html = """<div style="display:flex;align-items:center;gap:10px">
            <div style="font-weight:600">{gv}</div>
            <div style="background:#eef6ff;border-radius:6px;padding:3px 8px;font-size:12px;color:#1e5bbf">{badge}</div>
        </div>""".format(gv=frappe.utils.cstr(gv), badge=frappe.utils.cstr(badge_label))
        
        group_wise_status_total_hp = group_status_total_hp.get(gv, {})
        formatted_in_warrenty_hp = "{:,.0f}".format(group_wise_status_total_hp.get("IN Warranty", 0.0))
        formatted_out_warrenty_hp = "{:,.0f}".format(group_wise_status_total_hp.get("OUT Warranty", 0.0))
        formatted_amc_active_hp = "{:,.0f}".format(group_wise_status_total_hp.get("AMC Active", 0.0))
        formatted_amc_expired_hp = "{:,.0f}".format(group_wise_status_total_hp.get("AMC Expired", 0.0))
        
        group_wise_status_total_tonne = group_status_total_tonne.get(gv, {})
        formatted_in_warrenty_tonne = "{:,.0f}".format(group_wise_status_total_tonne.get("IN Warranty", 0.0))
        formatted_out_warrenty_tonne = "{:,.0f}".format(group_wise_status_total_tonne.get("OUT Warranty", 0.0))
        formatted_amc_active_tonne = "{:,.0f}".format(group_wise_status_total_tonne.get("AMC Active", 0.0))
        formatted_amc_expired_tonne = "{:,.0f}".format(group_wise_status_total_tonne.get("AMC Expired", 0.0))

        data.append({
            "group_label": gv,
            "group_html": group_html,
            "total_hp": total,
            "total_tonnes": tonnes,
            "total_hp_display": formatted_hp,
            "total_tonne_display": formatted_tonne,
            "product_count": count,
            "total_in_warrenty_hp": formatted_in_warrenty_hp,
            "total_out_warrenty_hp": formatted_out_warrenty_hp,
            "total_amc_active_hp": formatted_amc_active_hp,
            "total_amc_expired_hp": formatted_amc_expired_hp,
            "total_in_warrenty_tonne": formatted_in_warrenty_tonne,
            "total_out_warrenty_tonne": formatted_out_warrenty_tonne,
            "total_amc_active_tonne": formatted_amc_active_tonne,
            "total_amc_expired_tonne": formatted_amc_expired_tonne,
        })

    # columns (HTML first column + formatted display)
    columns = [
        {"fieldname": "group_html", "label": str({
            "Project": _("IL"),
            "Branch": _("Branch"),
            "AM": _("AM"),
            "Region": _("Region"),
            "RSM": _("RSM")
        }.get(group_by, group_by)), "fieldtype": "HTML", "width": 340},
        {"fieldname": "total_hp_display", "label": _("Total HP"), "fieldtype": "Data", "width": 140, "align": "right"},
        {"fieldname": "total_tonne_display", "label": _("Total Tonne"), "fieldtype": "Data", "width": 140, "align": "right"},
        {"fieldname": "total_hp", "label": _("Total HP (raw)"), "fieldtype": "Float", "hidden": True},
        {"fieldname": "total_tonnes", "label": _("Total Tonne (raw)"), "fieldtype": "Float", "hidden": True},
        {"fieldname": "total_in_warrenty_hp", "label": _("HP IN Warranty"), "fieldtype": "Data", "width": 190, "align": "right"},
        {"fieldname": "total_out_warrenty_hp", "label": _("HP OUT Warranty"), "fieldtype": "Data", "width": 190, "align": "right"},
        {"fieldname": "total_amc_active_hp", "label": _("HP AMC Active"), "fieldtype": "Data", "width": 190, "align": "right"},
        {"fieldname": "total_amc_expired_hp", "label": _("HP AMC Expired"), "fieldtype": "Data", "width": 190, "align": "right"},
        {"fieldname": "total_in_warrenty_tonne", "label": _("Tonne IN Warranty"), "fieldtype": "Data", "width": 190, "align": "right"},
        {"fieldname": "total_out_warrenty_tonne", "label": _("Tonne OUT Warranty"), "fieldtype": "Data", "width": 190, "align": "right"},
        {"fieldname": "total_amc_active_tonne", "label": _("Tonne AMC Active"), "fieldtype": "Data", "width": 190, "align": "right"},
        {"fieldname": "total_amc_expired_tonne", "label": _("Tonne AMC Expired"), "fieldtype": "Data", "width": 190, "align": "right"},
    ]

    # chart payload
    labels = [gv for gv, _ in sorted_groups]
    values_chart_tonne = [float(group_totals_tonne[gv]) for gv, _ in sorted_groups]
    values_chart = [group_status_total[gv] for gv, _ in sorted_groups]
    
    IN_Warranty = [values.get("IN Warranty", 0.0) for values in values_chart]
    OUT_Warranty = [values.get("OUT Warranty", 0.0) for values in values_chart]
    AMC_Active = [values.get("AMC Active", 0.0) for values in values_chart]
    AMC_Expired = [values.get("AMC Expired", 0.0) for values in values_chart]
    
    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("IN Warranty"), "values": IN_Warranty },
                {"name": _("OUT Warranty"), "values": OUT_Warranty},
                {"name": _("AMC Active"), "values": AMC_Active },
                {"name": _("AMC Expired"), "values": AMC_Expired},
            ]
        },
        "type": (filters.get("chart_type") or "bar"),
        "is_series": 1
    }

    # report summary
    report_summary = [{
        "value": "{:,.0f}".format(grand_total_hp),
        "indicator": "Green" if grand_total_hp > 0 else "Red",
        "label": _("Total HP (All)"),
        "datatype": "Data"
    }, {
        "value": "{:,.0f}".format(grand_total_tonnes),
        "indicator": "Green" if grand_total_tonnes > 0 else "Red",
        "label": _("Total Tonnes (All)"),
        "datatype": "Data"
    }, {
        "value": sum(group_counts.values()),
        "label": _("Total Product Rows"),
        "datatype": "Int"
    }]

    return columns, data, None, chart, report_summary