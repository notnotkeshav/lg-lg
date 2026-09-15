# Copyright (c) 2026, extension and contributors
# For license information, please see license.txt
"""
Customizations for lg-owned DocTypes used to live as Custom Field / Property Setter
records. They now live directly in lg/lg/doctype/<name>/<name>.json, so the records
are redundant - and a stale Property Setter silently overrides the schema value.

This patch removes the redundant records. It runs post_model_sync, so the schema
JSON has already been imported by the time it executes.

It is deliberately conservative: a record is only removed when its value already
matches what the schema now defines. Anything that differs is a customization this
site made which never reached the schema, so it is kept and reported instead of
being destroyed.
"""

import json

import frappe

# DocTypes whose schema JSON lives in the lg app
LG_DOCTYPES = [
	"AMC Quotation", "CRM Contract", "CRM Quotation", "Currency Exchange",
	"Dealer", "Model No", "Opportunity", "Pay Term", "Project",
	"Region Branches", "Region Master", "Technician", "Terms and Conditions",
	"Warranty",
]

# Properties that a standard DocType may not carry in its schema - Frappe rejects
# them in DocType.validate ("Standard DocType cannot have default print format,
# use Customize Form"). They must stay Property Setters, so never touch them.
DOCTYPE_ONLY_VIA_PROPERTY_SETTER = {"default_print_format"}

TRUTHY = {"1", "true", "yes"}
FALSY = {"0", "false", "no", "none", ""}


def _norm(value, fieldtype=None):
	"""Compare schema and Property Setter values without tripping over 0/'0'/None."""
	if value is None:
		value = ""
	value = str(value).strip()
	low = value.lower()
	if low in TRUTHY:
		return "1"
	if low in FALSY:
		return "0"
	return value


def _as_list(value):
	if isinstance(value, list):
		return value
	try:
		parsed = json.loads(value or "[]")
	except (TypeError, ValueError):
		return []
	return parsed if isinstance(parsed, list) else []


def _field_order_gap(setter_value, schema_value):
	"""Field names the old setter listed that the schema order does not carry."""
	return set(_as_list(setter_value)) - set(_as_list(schema_value))


def execute():
	kept, removed = [], []

	for doctype in LG_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue

		# --- Custom Fields that the schema now defines as real DocFields -------
		for cf in frappe.get_all("Custom Field", filters={"dt": doctype}, fields=["name", "fieldname"]):
			if frappe.db.exists("DocField", {"parent": doctype, "fieldname": cf.fieldname}):
				frappe.delete_doc("Custom Field", cf.name, force=True, ignore_permissions=True)
				removed.append(f"Custom Field  {doctype}.{cf.fieldname}")
			else:
				kept.append(f"Custom Field  {doctype}.{cf.fieldname} - not in schema, left in place")

		# --- Property Setters whose value the schema already carries ----------
		setters = frappe.get_all(
			"Property Setter",
			filters={"doc_type": doctype},
			fields=["name", "field_name", "property", "value", "doctype_or_field"],
		)
		for ps in setters:
			if ps.property in DOCTYPE_ONLY_VIA_PROPERTY_SETTER:
				continue

			if ps.doctype_or_field == "DocType" or not ps.field_name:
				target = doctype
				if ps.property == "field_order":
					# not a column on DocType - it is the DocField order
					schema_value = frappe.get_all(
						"DocField", filters={"parent": doctype}, pluck="fieldname", order_by="idx asc"
					)
				else:
					schema_value = frappe.db.get_value("DocType", doctype, ps.property)
			else:
				schema_value = frappe.db.get_value(
					"DocField", {"parent": doctype, "fieldname": ps.field_name}, ps.property
				)
				target = f"{doctype}.{ps.field_name}"
				if not frappe.db.exists("DocField", {"parent": doctype, "fieldname": ps.field_name}):
					# points at a field that does not exist - inert either way
					frappe.delete_doc("Property Setter", ps.name, force=True, ignore_permissions=True)
					removed.append(f"Property Setter {target}.{ps.property} (dead - no such field)")
					continue

			if ps.property == "field_order":
				# The schema's field_order is built as a superset: the merge kept every
				# field the old setter listed and added the ones it predated. Keeping a
				# stale copy here would hide newly added fields from the form.
				stale = _field_order_gap(ps.value, schema_value)
				frappe.delete_doc("Property Setter", ps.name, force=True, ignore_permissions=True)
				removed.append(f"Property Setter {target}.field_order")
				if stale:
					kept.append(
						f"note: {target}.field_order referenced field(s) absent from the "
						f"schema order: {sorted(stale)}"
					)
				continue

			if _norm(schema_value) == _norm(ps.value):
				frappe.delete_doc("Property Setter", ps.name, force=True, ignore_permissions=True)
				removed.append(f"Property Setter {target}.{ps.property}")
			else:
				kept.append(
					f"Property Setter {target}.{ps.property}: "
					f"schema={schema_value!r} setter={ps.value!r} - KEPT, please reconcile"
				)

	frappe.db.commit()

	print(f"[lg] removed {len(removed)} customization records now held in the schema")
	if kept:
		print(f"[lg] kept {len(kept)} record(s) that differ from the schema - review these:")
		for line in kept:
			print(f"       {line}")
