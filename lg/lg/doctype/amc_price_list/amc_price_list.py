# Copyright (c) 2024, extension and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AMCPriceList(Document):
    def validate(self):
        if self.enabled == 0:
            frappe.throw(_("This file does not exist"), frappe.ValidationError)
