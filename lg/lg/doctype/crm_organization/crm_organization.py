import frappe
from frappe import _
from frappe.model.naming import make_autoname

from crm.fcrm.doctype.crm_organization.crm_organization import CRMOrganization as BaseCRMOrganization


def get_customer_series(region, branch):
	return f"CUS-{region}-{branch}-.#####"


class CRMOrganization(BaseCRMOrganization):
	def autoname(self):
		# Takes precedence over the doctype's `field:naming_series` autoname,
		# giving CUS-<Region>-<Branch>-00001 with a separate counter per region/branch.
		if not self.region or not self.branch:
			frappe.throw(_("Region and Branch are required to generate the Customer ID"))

		self.name = make_autoname(get_customer_series(self.region, self.branch), doc=self)
		# keep the autoname field in sync with the name (doctype autoname is field:naming_series)
		self.naming_series = self.name
