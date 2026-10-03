# CRM / AMC Module Documentation

Covers: **CRM Deal**, **CRM Quotation**, **CRM Contract**, **CRM Organization**, **Dealer**, **Uploader**, **Pay Term**.

This documents the business process (Lead → Deal → Quotation → Contract → Invoice → Payment) implemented across the `crm` app (Frappe CRM, forked specifically for this project — upstream is `notnotkeshav/lg-crm`, **not** stock `frappe/crm`) and the `lg` app (LG-specific customization). Where a doctype lives matters: some doctypes are wholly owned by `lg`, some are base `crm` doctypes patched directly in the fork, and one (`CRM Deal`) is a base `crm` doctype with its Python controller class swapped out by `lg`.

> ⚠️ Several facts below (workflow states, some DB columns) exist only in the live site database, not in any file under `apps/`. They were confirmed by querying `lg.local` directly (`bench --site lg.local mariadb`). If you're reading this on a different site/environment, re-verify.

---

## 1. Where each doctype actually lives

| Doctype | App | Location | Pattern |
|---|---|---|---|
| CRM Deal | `crm` (base, forked) + `lg` (override) | `apps/crm/crm/fcrm/doctype/crm_deal/` (schema) + `apps/lg/lg/lg/doctype/crm_deal/crm_deal.py` (controller) | `hooks.py` → `override_doctype_class = {"CRM Deal": "lg.lg.doctype.crm_deal.crm_deal.CRMDeal"}`. The JSON schema is owned by `crm`; the Python controller is fully replaced by `lg`. |
| CRM Organization | `crm` (base, forked) | `apps/crm/crm/fcrm/doctype/crm_organization/` | Not overridden via hooks — the fork's own `crm_organization.py` has LG-specific code written directly into it (Excel import/export, duplicate-customer check, custom naming series). `lg` additionally layers ~10 Custom Fields (`custom_expected_hp`, `custom_expected_ton`, `project`, `warranty_expiry_date`, etc.) via fixtures. |
| CRM Quotation | `lg` (native) | `apps/lg/lg/lg/doctype/crm_quotation/` | Fully owned by `lg`. Submittable document. |
| CRM Contract | `lg` (native) | `apps/lg/lg/lg/doctype/crm_contract/` | Fully owned by `lg`. Submittable document. Only 3 Custom Fields on top (`custom_contract_status`, address HTML fields) — everything else is native. |
| Dealer | `lg` (native) | `apps/lg/lg/lg/doctype/dealer/` | Master doctype, no controller logic. |
| Uploader | `lg` (native) | `apps/lg/lg/lg/doctype/uploader/` | Not submittable; acts as a one-shot bulk-import "wizard" doctype. |
| Pay Term | `lg` (native) | `apps/lg/lg/lg/doctype/pay_term/` | Master doctype, no controller logic; its child table `Pay Term List` is the real payload. |

**Key implication for future changes:** if you need to add a field or behavior to `CRM Deal` or `CRM Organization`, decide first whether it belongs in the `crm` fork's doctype JSON/controller (if it's core to the field schema) or as a Custom Field / Client Script fixture in `lg` (if it's meant to be a lighter-weight customization). This codebase does **not** consistently pick one approach — see §7.

---

## 2. Business process flow (happy path)

```
CRM Organization (Customer)
        │
        ▼
   CRM Deal  ───────────────► (lost after 6 months past expiry → status "Lost")
        │  status: Qualification → Proposal/Quotation → Negotiation → Spec-In
        │          → Won/Award, driven by the linked Quotation (see §3 "Status &
        │          probability"); Ready to Close is manual
        │          (or Lost / Lost by AM / Lost by RSM)
        │  deal_category: "Service" (AMC/warranty) or "Sales"
        ▼
  CRM Quotation  (submittable; created from/against a Deal)
        │  workflow_state drives an approval matrix (see §3)
        │  on submit → "Create Sub Contract" button →
        │  crm.fcrm.doctype.crm_quotation.crm_quotation.make_crm_contract (mapped doc)
        ▼
  CRM Contract  (submittable)
        │  on_submit: pushes total_hp / amc_expiry_date / annual_revenue back onto
        │             the source CRM Deal; appends itself into the customer's
        │             CRM Organization.contracts_information child table;
        │             emails each row in the `dealer` child table for accept/reject
        │  billing_schedule (Contract Billing Schedule child table) generated from
        │             Pay Term + payment_frequency
        ▼
  Uploader (type=Invoice)  →  creates Invoice doc(s) from billing_schedule rows
        │
        ▼
  Uploader (type=Payment)  →  matches payments to Invoice.invoice_payment_term rows,
                               marks Invoice / Contract Billing Schedule Paid/Partially Paid
```

Renewal: `CRM Contract` has a (currently dead, see §7) `schedule_renewal_deal()` intended to auto-create a renewal `CRM Deal` 6 months before `expiry_date`. In practice, renewal today happens via the **"Renew"** button on an Expired/Discontinued Contract, which opens a new **AMC Term** document (not covered in this doc) linked back to the contract.

Every doctype in this flow that carries money (`CRM Quotation`, `CRM Contract`) shares the same **Contract Billing Schedule** child table, generated client-side from **Pay Term**, and the same **Region Master / Region Branches / Dealer** masters for territory and channel-partner assignment.

---

## 3. CRM Deal

**Files:** `apps/crm/crm/fcrm/doctype/crm_deal/crm_deal.json` (schema, extended in-fork with `amc_expiry_date`, `warranty_expiry_date`, `warranty_amc_status`, `project`, `product_details`, `total_hp`, `hp_under_amc`, `deal_category`, `from_contract`, etc.) · `apps/lg/lg/lg/doctype/crm_deal/crm_deal.py` (controller, via `override_doctype_class`).

- **Status** (`status`, Link → `CRM Deal Status`, default `Qualification`): `Qualification`, `Proposal/Quotation`, `Negotiation`, `Spec-In`, `Ready to Close`, `Won/Award`, `Lost`, `Lost by AM`, `Lost by RSM`, `Sales`.
- **`deal_category`** (Select, default `Service`): `Service` (AMC/warranty deals) vs `Sales`. Several hooks branch on this.

### Status & probability

`probability` is derived purely from `status` via `STATUS_PROBABILITY` in `crm_deal.py`, applied in `validate()` on every save. The Client Script **"Update Probability on deal status update"** mirrors the same table for the form (sets `probability` when the user changes `status`, and draws the progress banner on `refresh`). Keep the two tables in sync. The Client Script must **not** call `set_value` on `refresh` — that marks every opened record as "Not Saved".

| Status | Probability | How it's set |
|---|---|---|
| Qualification | 10% | Default for new deals; deals made from CRM Organization / CRM Contract (`make_crm_deal`, `create_renewal_deal`); **Interested** button on a Lost by AM/RSM deal |
| Proposal/Quotation | 40% | Quotation exists (Open / approval stages / Approved); **Create Quotation** button (only when deal is still Qualification) |
| Negotiation | 60% | Quotation `workflow_state` = Customer Approval Pending (quote sent to customer) |
| Spec-In | 80% | Quotation `workflow_state` = PO Pending / PO Received (customer accepted) |
| Ready to Close | 80% | Manual only |
| Won/Award | 100% | Quotation `workflow_state` = Quote Won (PO received, submitted) |
| Sales | 0% | `deal_category` set to Sales (Client Script "Deal category set Sales") |
| Lost by AM / Lost by RSM | 0% | **Not Interested** button — branch head (Service deals) / region head |
| Lost | 0% | **Not Interested** by final approver; or the daily expiry follow-up job (`lg/lg/expiry_follow_up.py`), 3 months after Warranty/AMC expiry |

Quote-driven changes come from `update_deal_status_from_quotation(quotation)` in `crm_deal.py`, called from `CRMQuotation.on_update` / `on_submit` / `on_update_after_submit` and from `update_workflow_to_sent` (which updates via raw SQL and so skips `on_update`). Rules:
- **Forward only**, in the order of `STATUS_PROGRESSION` (Qualification → Proposal/Quotation → Negotiation → Spec-In → Ready to Close → Won/Award). "Revise Quote" (back to Open) or a second quotation never moves a deal backwards.
- A `Rejected` quotation, or a cancelled one (`docstatus == 2`), changes nothing.
- Deals in `Lost`, `Lost by AM`, `Lost by RSM` or `Sales` are never touched.
- The deal is saved with `ignore_permissions` / `ignore_mandatory`, so `validate()` recomputes probability and logs the status change.

### Hooks (`CRMDeal` controller)

| Hook | What it does |
|---|---|
| `validate()` | Logs a status-change entry (`add_status_change_log`, from `crm`) when `status` changes on an existing doc. Sets `probability` from `status` (see "Status & probability"). Derives **`warranty_amc_status`** from expiry dates: if `amc_expiry_date` is set → `"AMC Active"`/`"AMC Expired"`; else if `warranty_expiry_date` is set → `"IN Warranty"`/`"OUT Warranty"`. If the deal is linked to a `Project`, pushes `expiry_date`/`status` onto that Project and saves it (`ignore_permissions=True`) **on every validate** — i.e. every save of a Deal re-saves its linked Project. |
| `after_save()` | Intended to recompute **`total_hp`** by summing `hp` across `product_details` — but `after_save` is **not a Frappe hook name**, so it never runs (see §7). `total_hp` is currently maintained only by the "Deal child product details" Client Script. |
| `after_insert()` / `on_update()` | Both call `update_project_status_if_latest()`: finds the most-recently-created `CRM Deal` for the same `project`; if *this* deal is that latest one, and it has the expiry date appropriate to its `deal_category` (`warranty_expiry_date` for Sales, `amc_expiry_date` for Service), pushes `status`/`current_deal`/`expiry_date` onto the `Project` via `frappe.db.set_value`. This exists alongside the similar-but-different Project sync in `validate()` — the two don't always agree (see §7). |

### Scheduled/whitelisted functions in this file

- `update_deal_status_from_quotation(quotation)` — quote-driven status sync; see "Status & probability" above.
- `get_performance_metrics()`, `get_recent_activities()` — whitelisted, used by dashboards (win rate, pipeline value, quotation conversion, contract renewal rate; last-7-days activity feed across Deal/Quotation/Contract).

### Warranty/AMC expiry follow-up (`lg/lg/expiry_follow_up.py`)

Daily job `run_expiry_follow_up()`. Covers AMC `CRM Contract`s and Warranty Deals linked to a `Project` (`warranty_expiry_date` + `project` set, no `amc_expiry_date`, no contract made from the deal yet). Starting 2 months before expiry, the responsible user gets a `CRM Task`, a system notification (`Notification Log`) and an email, once per stage. A stage only notifies within its first 7 days (`STAGE_NOTICE_DAYS`): that catches up missed runs, but doesn't flood users with a backlog of stages that started long ago.
- 0–1 month: AM (contract `user` / deal `deal_owner`, falling back to the branch head)
- 1–1.5 months: RSM (`Region Master.region_head`)
- 1.5 months up to the Lost date: HO (users with the `Alok` role)

3 months after expiry (of the deal itself, or of the contract it renews / was made from), a deal not in an engaged status (`Proposal/Quotation`…`Won/Award`), not `Lost` and not `Sales` is set to `Lost` via `save()`, so validate/status log run. Pending `Lost by AM`/`Lost by RSM` deals are finalized too. `reason` keeps the AM/RSM reason if there is one, else an automatic one. This is the only automatic Lost rule. `check_warranty_conversion` (crm fork) and `CRMContract.before_save` set the **category** `deal_type`/`contract_type` to "Lost … Conversion" on the same 3-month boundary, and they don't touch the status.

---

## 4. CRM Quotation

**Files:** `apps/lg/lg/lg/doctype/crm_quotation/{crm_quotation.json,crm_quotation.py,crm_quotation.js,api.py}`. Submittable, `naming_series = QT.-YYYY.-`.

### Approval workflow

`workflow_state` is a Custom Field (Frappe auto-adds this when a `Workflow` is attached). The live workflow is the **`Quote Approval Matrix 4`** `Workflow` document (DB-only — not exported to any file, so it must be manually recreated/migrated if you move sites):

```
Open ──(Submit for Approval)──► Approval Pending ──(Approve)──► Approved
Open ──(Submit for Approval)──► Yellow Zone Approval Pending
        │ (Yellow Zone Approve) ──► Approved
        │ (Yellow Zone Approve) ──► Orange Zone Approval Pending
        │       │ (Orange Zone Approve) ──► Approved
        │       │ (Orange Zone Approve) ──► Red Zone Approval Pending
        │       │       └ (Red Zone Approve) ──► Approved
        │       └ (Reject) ──► Rejected
        └ (Reject) ──► Rejected
Approval Pending ──(Reject)──► Rejected            [any zone-approver role]

Approved ──(Send Quote to Customer)──► Customer Approval Pending
Customer Approval Pending ──(Quote Accept)──► PO Pending
Customer Approval Pending ──(Revise Quote)──► Open
PO Pending ──(PO Receive)──► Quote Won             [docstatus → Submitted]
PO Received ──(Revise Quote)──► Open
```

Roles gating each zone: **Yellow/Orange/Red Zone Approver**. `zone` (Select: Green/Yellow/Orange/Red) and `required_approval` (Select: AM / AM+RSM / AM+RSM+Mr Alok / AM+RSM+Mr Alok+MD) on the doc drive which path a quote is routed down (routing logic itself lives in whatever sets `workflow_state`/`zone` initially — not in this controller).

### Client-side hooks (`crm_quotation.js`)

- `before_workflow_action(frm, action)` — **blocks the transition** (via `frappe.throw`) if: (a) leaving `PO Pending` without `uploaded` (PO document) checked, or (b) the current `workflow_state` requires zone remarks (`remarks`, `yellow_zone_approve_rejection_remarks`, `orange_zone_approve_rejection_remarks`, `red_zone_approve_rejection_remarks`) and the matching field is empty.
- `generate_billing_schedule(frm)` — fires on `start_date`, `end_date`, `payment_term`, `payment_frequency`, `billing_terms` change. Rebuilds the `billing_schedule` (Contract Billing Schedule) child table:
  - Special-cased `payment_frequency = "100% for Partial Contract"` → single row.
  - Otherwise steps from `start_date` to `end_date` in `Monthly`/`Quarterly`/`Semi-Annually`/`Annually` chunks; `billing_terms = "Advance"` bills at the start of each period, otherwise at the end.
  - `payment_date` on each row = billing date + the **minimum `days`** across the linked **Pay Term**'s `payment_term_portions`.
  - Year-1 amount = `amount`; year 2+ pulled positionally from the comma-separated `price_rate__as_per_year` field, falling back to `amount` if not enough values are supplied.
- `zone(frm)` / `fetch_price_rate_from_zone` / `show_filtered_zone_rates` — given `industry` (→ `CRM Industry.parent_vertical` → `Vertical Master.hp_and_zone_details`) and `total_hp`, looks up the matching HP-range row to auto-fill `zone` and `price_rate`.
- PDF/attachment widget in `refresh` — custom "Upload PDF" button + tabbed preview; on successful upload it force-sets `uploaded = 1` and saves if `status`/`workflow_state` isn't already `"PO Received"`.

### Server-side hooks (`crm_quotation.py`)

- `on_update()` — when `workflow_state` **changes into** `"Customer Approval Pending"`, auto-attaches a PDF (print format **"AMC Offer quote"**, or **"AMC Offer Quote Multi Year"** if `is_multi_year`) and emails it to the customer's `CRM Organization.email`. Then calls `update_deal_status_from_quotation` to advance the linked Deal's status (see §3).
- `on_submit()` / `on_update_after_submit()` — call `update_deal_status_from_quotation` (e.g. Quote Won → Deal `Won/Award`).
- `check_advance_payment_reminders()` — whitelisted + wired as a **daily scheduled job**. For every un-submitted (`docstatus=0`) quotation with `advance_amount`, finds the earliest unpaid `billing_schedule` row and, based on days overdue (1/20/25/30, or +60 for `is_govt`), emails the owner (`send_advance_reminder`) and past the threshold force-sets `custom_contract_status = "Discontinue"` on... **a `CRM Contract`** with the same name (`mark_or_notify_discontinuation` writes to `"CRM Contract"`, not `"CRM Quotation"` — a copy-paste artifact from the equivalent Contract function, see §7).
- `send_zone_approval_alert_api(docname)` — whitelisted. Given the current `workflow_state`, maps to a zone-approver role, creates a `Notification Log` for every user with that role, and emails them. This is **not called automatically** anywhere in this codebase — it must be invoked explicitly (e.g. from a workflow action's client script or an external call).
- `update_workflow_to_sent(docname)` — whitelisted. Force-moves `Approved → Customer Approval Pending` via **raw SQL**, bypassing all Workflow/Document validation and hooks, then adds a tracking comment and explicitly calls `update_deal_status_from_quotation` (Deal → `Negotiation`). Note it does **not** send the customer email that `on_update()` would.
- `get_zone_from_vertical_master(...)` — server-side equivalent of the JS zone lookup; also computes `amc_year`/`amc_term` from date range.

### `Create Sub Contract` button

Visible once `docstatus == 1` (submitted). Calls `crm.fcrm.doctype.crm_quotation.crm_quotation.make_crm_contract` (mapped-doc, defined in the `crm` app) to spin up a `CRM Contract` pre-filled from the quotation.

---

## 5. CRM Contract

**Files:** `apps/lg/lg/lg/doctype/crm_contract/{crm_contract.json,crm_contract.py,crm_contract.js,api.py}`. Submittable, `naming_series = CNT-.YYYY.-`.

**⚠️ Controller quirk:** `crm_contract.py` defines **`class CRMContract(Document):` three times** in the same module. In Python, each class statement rebinds the name — Frappe only ever sees the **last** one when it does `getattr(module, "CRMContract")`. That means:
- The **first** class body (`on_submit` → `schedule_renewal_deal` / `create_renewal_deal` / `update_serial_no`) is **dead code**. Auto-creating a renewal Deal 6 months before expiry, and syncing warranty days onto the `Serial No` record, **do not currently run**, despite looking like active logic.
- The **second** class body (`default_list_data`) is also dead.
- Only the **third** class body is live: `on_update_after_submit`, `on_submit` (→ `set_hp_in_deal_and_expiry_date`, `send_contract_email_on_submit`, `set_contract_in_customer`), `before_validate`, `validate`, `before_save`, `set_status`, `validate_dates`, `validate_currency`.

If you need the renewal-deal-on-submit or Serial No sync behavior, it has to be re-added to the third class (or the file split up) — don't assume it fires today.

### Active hooks (third `CRMContract` class)

| Hook | What it does |
|---|---|
| `before_validate` → `set_status()` | If `custom_contract_status` is empty, sets it to `Expired` (if `expiry_date` is past) or `Active`. Never overrides an already-set status. |
| `validate()` | `validate_dates()` (start ≤ expiry, else throws), `validate_currency()` (auto-sets `conversion_rate`/`price_list_exchange_rate` — `1.0` if `currency == price_list_currency`, else via `get_exchange_rate`), `set_status()` again. |
| `before_save()` | If `from_deal` is set: if that Deal has no prior `from_contract`, copies `deal_type` → `contract_type`. Otherwise compares today against the **previous** contract's `expiry_date + 3 months` to decide `contract_type = "Lost AMC Conversion"` vs `"AMC Renewable"`. |
| `on_submit()` | `set_hp_in_deal_and_expiry_date()` — pushes `total_hp`, `amc_expiry_date` (=`expiry_date`), `annual_revenue` (=`amount`), and `duplicate_trigger_date` (=`expiry_date` − 1 month) back onto the linked `from_deal`. `send_contract_email_on_submit()` — emails every row in the `dealer` child table (print format **"AMC Offer"**, PDF attached) with Accept/Reject links pointing at `accept_contract` / `reject_contract`. `set_contract_in_customer()` — appends a row (`contract_id`, `start_date`, `expiry_date`, `status`) into the customer's `CRM Organization.contracts_information` child table and saves it. |
| `on_update_after_submit()` | Compares the `dealer` child table against `self._doc_before_save`; if a row's `commission_rate` changed, emails that dealer (`send_commission_update_email`) with Accept/Reject links. |

### Whitelisted endpoints (`crm_contract.py`)

- `accept_contract(docname, dealer_id)` / `reject_contract(docname, dealer_id)` — **`allow_guest=True`** (called from email links, no login). Sets the matching `dealer` row's `status`, sets `custom_contract_status` on the whole contract, saves with `ignore_permissions=True`. `accept_contract` additionally notifies the dealer + the contract's `Region Master.region_head` + everyone with the **Finance** role.
- `check_advance_payment_reminders()` — same pattern as the Quotation version; daily scheduled job (`hooks.py`). Escalates to `mark_or_notify_discontinuation` which (correctly, this time) sets `custom_contract_status = "Discontinue"` on the **CRM Contract** itself.
- `check_billing_schedule_and_notify()` — daily scheduled job. Walks non-Discontinued contracts' `billing_schedule`; for rows with `is_advance == 0` and `status == "Pending"`, sends an overdue-payment email (hardcoded recipient `payal@extensioncrm.com`, not the contract owner) at day 30 (non-govt) / day 60 (govt), and calls `mark_contract_discontinue()` past 60 days for either.
- `set_status_expired()` — daily scheduled job. Force-sets `custom_contract_status = "Expired"` for any contract whose `expiry_date` has passed and isn't already `Expired`/`Discontinue`.
- `process_invoice_excel(file_url)` — bulk-updates `billing_schedule` rows (marks `Paid`, sets `invoice_id`/`amount_received`) by matching an uploaded Excel's `customer_po_id` against `CRM Contract.customer_po_id`.
- `upload_product_details(file_url, docname)` — replaces `product_details` from an uploaded CSV.
- `make_crm_deal(source_name, target_doc)` — mapped-doc helper to spin a new `CRM Deal` off a Contract (used for manual renewal flows).

### Client-side (`crm_contract.js`)

- **"Renew"** button appears when `custom_contract_status` is `Expired`/`Discontinue` **and** no `AMC Term` already references this contract (`reference_contract`); opens a new `AMC Term` pre-filled with `customer`/`reference_contract`.
- "Download/Upload Product Template" buttons — CSV round-trip for `product_details`, calling `upload_product_details` server method above.
- `validate()` client hook recomputes `total_hp` from `product_details` client-side (separate from, and redundant with, any server-side total).
- Activity/task/follow-up mini-CRM widget rendered into the form (task list, follow-ups, completion dialogs) — self-contained UI backed by `frappe.call`s to Frappe's generic Activity APIs, not part of the AMC data model.

---

## 6. CRM Organization, Dealer, Uploader, Pay Term

### CRM Organization
Base doctype lives in the `crm` fork (`apps/crm/crm/fcrm/doctype/crm_organization/`), extended with `lg` Custom Fields (`custom_expected_hp`, `custom_expected_ton`, `project`, `warranty_expiry_date`, plus layout-only section/column breaks). Represents the **Customer**.

- `before_insert` → `set_naming_series()`: builds a human-readable code from the first 3 letters of `organization_name` + `site_location_city` + creation date (e.g. `abc-delhi-2026-07-08`) and stores it in `naming_series` (a plain Data field here, not a Frappe naming-series field).
- `before_save`: throws if another `CRM Organization` already exists with the same `organization_name` + `project` + `branch` (duplicate-customer guard).
- Receives writes from both `CRM Contract.set_contract_in_customer()` (appends to `contracts_information`) and `Dealer`/`Dealer Team` (via the `dealer_team` child table).
- `import_excel_crm_organization` / `download_excel_template`: bulk customer + `Customer Visit Form` child-row import from `.xlsx`, with flexible header-to-fieldname resolution (label match → scrubbed label → alias table → literal fieldname) and upsert-by-`customer_hc` (falls back to `organization_name`+`branch`).

### Dealer
Pure master (`apps/lg/lg/lg/doctype/dealer/`) — no `validate`/hooks in `dealer.py` (`pass`), no client script. Fields: `dealer_name`, `customer_type` (Residential/Commercial/Individual), `commission_rate`, `lccasp` (LCC/ASP/AMC), `region`/`branch`, `dealer_visits` (child table). Referenced by:
- `CRM Contract.dealer` (Dealer Team child rows) — commission tracking + accept/reject emailing.
- `Dealer` is looked up by `dealer_id` in those flows; `Dealer.email_id` is the target for contract/commission emails.

### Uploader
Not submittable — a disposable "run an import" doctype (`apps/lg/lg/lg/doctype/uploader/`) with a `Select` (`Invoice`/`Payment`) plus two child tables (`invoice_uploader`, `payment_uploader`) that only one of which is populated at a time.

- **Client (`uploader.js`)**: changing `upload` calls `get_invoice_upload_data` or `get_payment_upload_data` and fills the matching child table from the response (does not touch the DB — read-only fetch).
- **Server (`after_insert`)**: this is where the actual writes happen, only once the Uploader doc is *saved* (inserted):
  - `upload == "Invoice"`: for each `invoice_uploader` row (skips rows with no `contract_id` or a duplicate `invoice_id`), creates a new **Invoice** doc, expands it into `invoice_payment_term` rows using the linked **Pay Term**'s portions (`invoice_portion` % of the billed amount, due date = billing date + portion's `days`), then finds the matching `Contract Billing Schedule` row (matched by exact `billing_date` + `amount`) and stamps it `status = "Invoice Raised"` with the new invoice's id/link.
  - `upload == "Payment"`: for each `payment_uploader` row, finds the `Invoice`, applies the received amount to the `invoice_payment_term` row whose `due_date` is today-or-earlier and whose `portion_amount` matches, recomputes the Invoice's `total_paid`/`total_outstanding`/`status` (`Paid` if fully received, else `Partially Paid`), and pushes that status onto the matching `Contract Billing Schedule` row.
- Both branches are wrapped in one big `try/except` that re-throws on any failure — a bad row anywhere in the batch can abort the whole Uploader save after partially processing earlier rows (no per-row transaction boundary beyond Frappe's own).

### Pay Term
Master (`apps/lg/lg/lg/doctype/pay_term/`) with one child table, **Pay Term List** (`payment_term_portions`): `invoice_portion` (%) and `days`. This is the single source of truth consumed by:
- `CRM Quotation.generate_billing_schedule` (JS) — payment due-date offset.
- `CRM Contract`/`Uploader.after_insert` — splitting an invoiced amount into `invoice_payment_term` portions.
- `update_invoice_due_dates` (in `crm_contract.py`) — recomputes `Invoice Payment Term.due_date` for every portion from a given `billed_date`.

No controller logic of its own (`pay_term.py` is a bare `pass`).

---

## 7. Known inconsistencies (read before extending this code)

These aren't hypothetical — they were confirmed against the live `lg.local` site schema and are easy to trip over:

1. **`CRM Contract`'s first two `class CRMContract(Document):` bodies are dead code** (see §5). `schedule_renewal_deal`/`create_renewal_deal`/`update_serial_no` never run on submit today.
2. **`CRM Contract Billing Schedule`'s DB table has columns with no matching field metadata.** `payment_date`, `is_advance`, `is_discountinue`, `amount_received`, `payment_received_date`, `invoice_portion`, `outstanding_amount`, `exchange_rate`, `amount_usd`, `is_free` all exist as real MySQL columns (confirmed via `DESCRIBE`), but there is **no** `Custom Field` record and **no** entry in the doctype JSON for any of them — they're invisible to `frappe.get_meta()`. Code that reads/writes them via `row.fieldname` (both in `crm_quotation.js`/`crm_contract.py` reminder logic) is relying on fields Frappe itself doesn't know exist. If you touch billing-schedule reminder/advance-payment logic, verify field-by-field against `DESCRIBE \`tabContract Billing Schedule\`` rather than trusting the doctype JSON.
3. **`CRM Quotation.mark_or_notify_discontinuation` writes to `"CRM Contract"`, not `"CRM Quotation"`** — almost certainly copy-pasted from the Contract version of the same function and never adjusted. A quotation's own advance-payment breach ends up flipping a same-named Contract's status instead.
4. **Project-status sync for `CRM Deal` is duplicated and can disagree**: `validate()` unconditionally overwrites the linked `Project`'s `status`/`expiry_date` from whichever expiry field is set, while `update_project_status_if_latest()` (in `after_insert`/`on_update`) only does so if this Deal is the *latest* one for the project **and** has the category-appropriate expiry field. Since `validate()` always runs before save regardless of "latest", an older Deal being edited can still overwrite the Project's status.
5. **`CRM Organization` vs. `CRM Deal`**: the `crm` app here is a **project-specific fork** (`notnotkeshav/lg-crm`), not stock Frappe CRM — it already has LG/AMC fields baked directly into its own doctype JSON and controllers (e.g. `crm_organization.py`'s Excel import functions, `crm_deal.json`'s `amc_expiry_date`/`warranty_amc_status`/`product_details`). Only `CRM Deal`'s controller is swapped via `override_doctype_class`; `CRM Organization`'s controller is edited in place in the fork. Don't assume "anything in `apps/crm` is untouched upstream code" — check before treating it as a read-only vendor dependency.
6. **`CRMDeal.after_save()` never runs** — `after_save` is not a Frappe controller hook (the real one is `on_update`). Its `total_hp` recalculation is dead code; also note it uses `int(row.hp)` while the Client Script uses `parseFloat`, so the two would disagree on fractional HP if it were wired up.
