import frappe
from frappe import _
from frappe.model.document import Document
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import add_status_change_log

from frappe.utils import (
    add_months,
    get_first_day,
    get_last_day,
    nowdate,
    getdate,
    today
)

class CRMDeal(Document):
    def validate(self):
        if not self.is_new():
            if self.has_value_changed("status"):
                add_status_change_log(self)
                
        current_date = getdate(today())
        if self.amc_expiry_date:
            expiry_date = getdate(self.amc_expiry_date)
            if expiry_date > current_date:
                self.warranty_amc_status = "AMC Active"
            else:
                self.warranty_amc_status = "AMC Expired"
        elif self.warranty_expiry_date:
            expiry_date = getdate(self.warranty_expiry_date)
            if expiry_date > current_date:
                self.warranty_amc_status = "IN Warranty"
            else:
                self.warranty_amc_status = "OUT Warranty"

        if self.project:
            project_doc = frappe.get_doc("Project", self.project)
            # project_doc.current_deal = self.name
            if self.warranty_expiry_date:
                project_doc.expiry_date = self.warranty_expiry_date
                project_doc.status = self.warranty_amc_status

            if self.amc_expiry_date:
                project_doc.expiry_date = self.amc_expiry_date
                project_doc.status = self.warranty_amc_status

            project_doc.save(ignore_permissions=True)


       

    # your_app/your_app/api/warranty_status_checker.py


        
    def after_save(self):
        frappe.logger().info("✅ CRMDeal after_save triggered")
        total = 0
        if self.product_details:
            for row in self.product_details:
                if row.hp is not None:
                    try:
                        total += int(row.hp)
                    except ValueError:
                        frappe.throw(f"Invalid HP value in row {row.idx}")
        frappe.db.set_value(self.doctype, self.name, "total_hp", total)


            


    # def update_project_status_if_latest(self):
    #     if self.project:
    #         latest_deal = frappe.db.get_value(
    #             "CRM Deal",
    #             {"project": self.project},
    #             ["name", "warranty_amc_status"],
    #             order_by="creation desc"
    #         )

    #         if latest_deal and latest_deal[0] == self.name:
    #             frappe.db.set_value("Project", self.project, {
    #                 "status": self.warranty_amc_status,
    #                 "current_deal": self.name
    #             })

    #             # Set expiry date based on available field
    #             expiry_date = self.amc_expiry_date or self.warranty_expiry_date
    #             if expiry_date:
    #                 frappe.db.set_value("Project", self.project, "expiry_date", expiry_date)

    #             frappe.msgprint(
    #                 f"Updated Project {self.project}:\n"
    #                 f"- Status: {self.warranty_amc_status}\n"
    #                 f"- Current Deal: {self.name}\n"
    #                 f"- Expiry Date: {expiry_date}"
    #             )

    def update_project_status_if_latest(self):
        if not self.project:
            return

        # Get the latest deal for the same project
        latest_deal = frappe.db.get_value(
            "CRM Deal",
            {"project": self.project},
            ["name", "deal_category", "warranty_amc_status", "warranty_expiry_date", "amc_expiry_date"],
            order_by="creation desc"
        )

        if not latest_deal:
            return

        (
            latest_name,
            deal_category,
            status,
            warranty_expiry,
            amc_expiry
        ) = latest_deal

        # Check if current deal is the latest
        if latest_name != self.name:
            return

        # 🧠 Based on category, pick only if expiry date exists
        if (deal_category == "Sales" and warranty_expiry) or (deal_category == "Service" and amc_expiry):
            # Update project fields
            frappe.db.set_value("Project", self.project, {
                "status": status,
                "current_deal": self.name,
                "expiry_date": amc_expiry if deal_category == "Service" else warranty_expiry
            })



        
            

    def after_insert(self):
        self.update_project_status_if_latest()

    def on_update(self):
        self.update_project_status_if_latest()



@frappe.whitelist()
def get_performance_metrics():
    """
    Calculate performance metrics for the dashboard
    
    Returns:
        dict: Dictionary containing performance metrics
    """
    try:
        today = frappe.utils.today()
        current_month_start = frappe.utils.get_first_day(today)
        current_month_end = frappe.utils.get_last_day(today)
        last_month_start = frappe.utils.get_first_day(frappe.utils.add_months(today, -1))
        last_month_end = frappe.utils.get_last_day(frappe.utils.add_months(today, -1))
        
        # Deal metrics
        current_month_deals = frappe.db.count("CRM Deal", filters={
            "creation": ["between", [current_month_start, current_month_end]]
        }) or 0
        
        last_month_deals = frappe.db.count("CRM Deal", filters={
            "creation": ["between", [last_month_start, last_month_end]]
        }) or 0
        
        current_month_won_deals = frappe.db.count("CRM Deal", filters={
            "creation": ["between", [current_month_start, current_month_end]],
            "status": "Closed Won"
        }) or 0
        
        last_month_won_deals = frappe.db.count("CRM Deal", filters={
            "creation": ["between", [last_month_start, last_month_end]],
            "status": "Closed Won"
        }) or 0
        
        # Calculate deal win rate
        deal_win_rate = 0
        if current_month_deals > 0:
            deal_win_rate = (current_month_won_deals / current_month_deals) * 100
        
        last_month_win_rate = 0
        if last_month_deals > 0:
            last_month_win_rate = (last_month_won_deals / last_month_deals) * 100
        
        win_rate_trend = deal_win_rate - last_month_win_rate
        
        # Pipeline metrics
        pipeline_value = frappe.db.sql("""
            SELECT SUM(annual_revenue) 
            FROM `tabCRM Deal` 
            WHERE status NOT IN ('Closed Lost', 'Cancelled')
        """)[0][0] or 0
        
        last_month_pipeline = frappe.db.sql("""
            SELECT SUM(annual_revenue) 
            FROM `tabCRM Deal` 
            WHERE modified BETWEEN %s AND %s
            AND status NOT IN ('Closed Lost', 'Cancelled')
        """, [last_month_start, last_month_end])[0][0] or 0
        
        pipeline_trend = ((pipeline_value - last_month_pipeline) / (last_month_pipeline or 1)) * 100
        
        # Quotation metrics
        current_month_quotations = frappe.db.count("CRM Quotation", filters={
            "creation": ["between", [current_month_start, current_month_end]]
        }) or 0
        
        current_month_converted = frappe.db.count("CRM Quotation", filters={
            "creation": ["between", [current_month_start, current_month_end]],
            "status": "Converted"
        }) or 0
        
        last_month_quotations = frappe.db.count("CRM Quotation", filters={
            "creation": ["between", [last_month_start, last_month_end]]
        }) or 0
        
        last_month_converted = frappe.db.count("CRM Quotation", filters={
            "creation": ["between", [last_month_start, last_month_end]],
            "status": "Converted"
        }) or 0
        
        # Calculate quotation conversion rate
        quotation_conversion_rate = 0
        if current_month_quotations > 0:
            quotation_conversion_rate = (current_month_converted / current_month_quotations) * 100
        
        last_month_conversion_rate = 0
        if last_month_quotations > 0:
            last_month_conversion_rate = (last_month_converted / last_month_quotations) * 100
        
        conversion_trend = quotation_conversion_rate - last_month_conversion_rate
        
        # Contract metrics
        active_contracts = frappe.db.count("CRM Contract", filters={"status": "Active"}) or 0
        total_contracts = frappe.db.count("CRM Contract") or 0
        
        contract_renewal_rate = 0
        if total_contracts > 0:
            contract_renewal_rate = (active_contracts / total_contracts) * 100
        
        # Helper function to determine status label
        def get_status_label(value, thresholds):
            if value >= thresholds["good"]:
                return "good"
            elif value >= thresholds["average"]:
                return "average"
            else:
                return "poor"
        
        # Prepare metrics
        metrics = [
            {
                "id": "deal_win_rate",
                "title": "Deal Win Rate",
                "value": round(deal_win_rate, 1),
                "unit": "%",
                "status": get_status_label(deal_win_rate, {"good": 30, "average": 20}),
                "progress": min(deal_win_rate, 100) / 100,
                "trend": win_rate_trend
            },
            {
                "id": "pipeline_value",
                "title": "Pipeline Value",
                "value": pipeline_value,
                "unit": "currency",
                "status": get_status_label(pipeline_value, {"good": 1000000, "average": 500000}),
                "progress": min(pipeline_value / 2000000, 1),
                "trend": pipeline_trend
            },
            {
                "id": "quotation_conversion",
                "title": "Quotation Conversion",
                "value": round(quotation_conversion_rate, 1),
                "unit": "%",
                "status": get_status_label(quotation_conversion_rate, {"good": 50, "average": 30}),
                "progress": min(quotation_conversion_rate, 100) / 100,
                "trend": conversion_trend
            },
            {
                "id": "contract_renewal",
                "title": "Contract Renewal Rate",
                "value": round(contract_renewal_rate, 1),
                "unit": "%",
                "status": get_status_label(contract_renewal_rate, {"good": 70, "average": 50}),
                "progress": min(contract_renewal_rate, 100) / 100,
                "trend": 0
            }
        ]
        
        return {"metrics": metrics}
    
    except Exception as e:
        frappe.log_error(f"Error in get_performance_metrics: {str(e)}")
        return {"metrics": []}

@frappe.whitelist()
def get_recent_activities():
    """
    Get recent activities related to deals, quotations, and contracts
    
    Returns:
        list: List of recent activities with details
    """
    try:
        # Get activities from the last 7 days
        date_filter = ["modified", ">", frappe.utils.add_days(frappe.utils.nowdate(), -7)]
        
        # Get recent deals
        deals = frappe.get_all(
            "CRM Deal",
            filters=[date_filter],
            fields=["name", "status", "modified", "customer", "annual_revenue"]
        )
        
        # Get recent quotations
        quotations = frappe.get_all(
            "CRM Quotation",
            filters=[date_filter],
            fields=["name", "status", "modified", "customer", "grand_total"]
        )
        
        # Get recent contracts
        contracts = frappe.get_all(
            "CRM Contract",
            filters=[date_filter],
            fields=["name", "status", "modified", "customer", "contract_value"]
        )
        
        # Combine and format activities
        activities = []
        
        for deal in deals:
            activities.append({
                "id": deal.name,
                "type": "deal",
                "description": f"Deal {deal.name} for {deal.customer or 'Unknown'} was updated",
                "date": deal.modified,
                "link": f"/app/crm-deal/{deal.name}"
            })
        
        for quotation in quotations:
            activities.append({
                "id": quotation.name,
                "type": "quotation",
                "description": f"Quotation {quotation.name} for {quotation.customer or 'Unknown'} was updated",
                "date": quotation.modified,
                "link": f"/app/crm-quotation/{quotation.name}"
            })
        
        for contract in contracts:
            activities.append({
                "id": contract.name,
                "type": "contract",
                "description": f"Contract {contract.name} for {contract.customer or 'Unknown'} was updated",
                "date": contract.modified,
                "link": f"/app/crm-contract/{contract.name}"
            })
        
        # Sort by date (newest first) and limit to 10 activities
        activities.sort(key=lambda x: x["date"], reverse=True)
        activities = activities[:10]
        
        return {"activities": activities}
    
    except Exception as e:
        frappe.log_error(f"Error in get_recent_activities: {str(e)}")
        return {"activities": []} 



def mark_deals_as_lost():
    current_date = getdate(today())
    deals =frappe.get_all("CRM Deal",filters={"status":["not in",["Proposal/Quotation", "Won/Award","Lost"]]},fields=["name","warranty_expiry_date","amc_expiry_date","status"])
    for deal in deals:
        expiry_date = None
        if deal.warranty_expiry_date:
            expiry_date = deal.warranty_expiry_date
        elif deal.amc_expiry_date:
            expiry_date=deal.amc_expiry_date
        if expiry_date:
            six_months_after=add_months(expiry_date,6)
            if six_months_after<=current_date:
                frappe.db.set_value("CRM Deal",deal.name,"status","Lost")
    frappe.db.commit()