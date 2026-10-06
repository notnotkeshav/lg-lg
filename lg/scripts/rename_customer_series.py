"""
One-off: rename existing CRM Organization (customer) records to the
CUS-<Region>-<Branch>-##### series and repoint everything linked to them.

Nothing linked is loaded or saved as a document. Links are rewritten in place
with frappe.db.set_value / plain UPDATEs, so submitted/cancelled CRM Contracts,
docs with missing mandatory fields, broken links etc. don't raise errors.

Usage (from the bench root):

    # dry run: does the full rename inside a transaction, prints the summary, then rolls back
    bench --site <site> execute lg.scripts.rename_customer_series.execute

    # actually apply
    bench --site <site> execute lg.scripts.rename_customer_series.execute --kwargs "{'dry_run': 0}"

Take a DB backup first (`bench --site <site> backup`) and run it while users
aren't creating customers. Re-running is safe: records already on the new
series are skipped. A CSV of old -> new names is written to the site's
private/files folder.
"""

import csv
import re

import frappe
from frappe.model.naming import make_autoname
from frappe.model.rename_doc import (
	get_link_fields,
	rename_dynamic_links,
	rename_versions,
	update_attachments,
)
from frappe.utils import cint, now_datetime

from lg.lg.doctype.crm_organization.crm_organization import get_customer_series

DOCTYPE = "CRM Organization"
SAVEPOINT = "rename_customer"


def execute(dry_run=1, commit_every=100):
	dry_run = cint(dry_run)
	commit_every = cint(commit_every) or 100

	orgs = frappe.get_all(
		DOCTYPE,
		fields=["name", "region", "branch"],
		order_by="creation asc, name asc",
	)
	link_fields = _get_link_fields()

	log = []
	renamed = failed = skipped = contracts_updated = 0

	for i, org in enumerate(orgs, 1):
		old = org.name

		if not org.region or not org.branch:
			skipped += 1
			log.append([old, "", org.region, org.branch, 0, "skipped: region/branch missing"])
			continue

		if _is_on_new_series(old, org.region, org.branch):
			skipped += 1
			log.append([old, old, org.region, org.branch, 0, "skipped: already on new series"])
			continue

		frappe.db.savepoint(SAVEPOINT)
		try:
			new = _next_name(org.region, org.branch)
			n_contracts = _rename(old, new, link_fields)
		except Exception as e:
			frappe.db.rollback(save_point=SAVEPOINT)
			failed += 1
			log.append([old, "", org.region, org.branch, 0, f"failed: {e}"])
			continue

		renamed += 1
		contracts_updated += n_contracts
		log.append([old, new, org.region, org.branch, n_contracts, "renamed"])

		if not dry_run and i % commit_every == 0:
			frappe.db.commit()
			print(f"... {i}/{len(orgs)} processed")

	if dry_run:
		frappe.db.rollback()
	else:
		frappe.db.commit()
		frappe.clear_cache()
		frappe.enqueue("frappe.utils.global_search.rebuild_for_doctype", doctype=DOCTYPE)

	log_path = _write_log(log, dry_run)

	print(
		f"{'DRY RUN (rolled back) - ' if dry_run else ''}"
		f"customers: {len(orgs)}, renamed: {renamed}, skipped: {skipped}, failed: {failed}, "
		f"contracts repointed: {contracts_updated}"
	)
	print(f"log: {log_path}")
	for row in log:
		if row[5].startswith("failed"):
			print("  ", row[0], row[5])


def _rename(old, new, link_fields):
	"""Rename one customer and repoint every link to it. Returns number of contracts updated."""
	# the customer row itself (+ naming_series, which is the doctype's autoname field)
	frappe.db.sql(
		f"update `tab{DOCTYPE}` set name=%s, naming_series=%s where name=%s",
		(new, new, old),
	)
	# its own child tables (contracts_information, dealer_team, project_info, ...)
	for df in frappe.get_meta(DOCTYPE).get_table_fields():
		frappe.db.sql(
			f"update `tab{df.options}` set parent=%s where parent=%s and parenttype=%s",
			(new, old, DOCTYPE),
		)

	# CRM Contract - row by row with set_value, no doc load/save, so submitted docs are fine
	contracts = frappe.get_all("CRM Contract", filters={"customer": old}, pluck="name")
	for contract in contracts:
		frappe.db.set_value("CRM Contract", contract, "customer", new, update_modified=False)

	# every other Link field pointing to CRM Organization (Deal, Quotation, Warranty, Project, child tables, custom fields...)
	for field in link_fields:
		if field.issingle:
			if frappe.db.get_single_value(field.parent, field.fieldname) == old:
				frappe.db.set_single_value(field.parent, field.fieldname, new, update_modified=False)
		else:
			frappe.db.set_value(
				field.parent, {field.fieldname: old}, field.fieldname, new, update_modified=False
			)

	# Dynamic Links (Address/Contact links, Comment, ToDo, Communication, ...), attachments, version history
	rename_dynamic_links(DOCTYPE, old, new)
	update_attachments(DOCTYPE, old, new)
	rename_versions(DOCTYPE, old, new)

	return len(contracts)


def _get_link_fields():
	fields = []
	for f in get_link_fields(DOCTYPE):
		f = frappe._dict(f)
		if (f.parent, f.fieldname) == ("CRM Contract", "customer"):
			continue  # handled explicitly
		if not f.issingle and not frappe.db.table_exists(f.parent):
			continue
		fields.append(f)
	return fields


def _next_name(region, branch):
	series = get_customer_series(region, branch)
	name = make_autoname(series, DOCTYPE)
	# guard against the counter lagging behind names created some other way
	while frappe.db.exists(DOCTYPE, name):
		name = make_autoname(series, DOCTYPE)
	return name


def _is_on_new_series(name, region, branch):
	return bool(re.fullmatch(rf"CUS-{re.escape(region)}-{re.escape(branch)}-\d{{5,}}", name))


def _write_log(rows, dry_run):
	stamp = now_datetime().strftime("%Y%m%d_%H%M%S")
	path = frappe.get_site_path(
		"private", "files", f"customer_rename_{'dryrun_' if dry_run else ''}{stamp}.csv"
	)
	with open(path, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(["old_name", "new_name", "region", "branch", "contracts_updated", "status"])
		writer.writerows(rows)
	return path
