// Copyright (c) 2025, Extension Technology Pvt Ltd
// For license information, please see license.txt

frappe.query_reports["AR Ageing Report"] = {
  "filters": [
    {
      "fieldname": "branch",
      "label": __("Branch"),
      "fieldtype": "Link",
      "options": "Region Branches",
      "reqd": 0
    },
    {
      "fieldname": "region",
      "label": __("Region"),
      "fieldtype": "Link",
      "options": "Region Master",       // ✅ Added missing link option
      "reqd": 0
    },
    {
      "fieldname": "name",
      "label": __("Customer Name"),
      "fieldtype": "Link",
      "options": "CRM Organization",     // ✅ Updated to correct doctype
      "reqd": 0
    },
    {
      "fieldname": "project",
      "label": __("Project"),
      "fieldtype": "Link",
      "options": "Project",
      "reqd": 0
    }
  ]
};
