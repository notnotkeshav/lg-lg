from frappe import _


def get_data(data):
	"""Add a Connections tab to CRM Organization) listing its CRM Contracts."""
	# the form only fetches connection counts when a default fieldname is set
	data.fieldname = data.get("fieldname") or "customer"
	data.setdefault("non_standard_fieldnames", {})["CRM Contract"] = "customer"
	data.setdefault("transactions", []).append({"label": _("Contracts"), "items": ["CRM Contract"]})
	return data
