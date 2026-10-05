// Copyright (c) 2026, extension and contributors
// For license information, please see license.txt

frappe.query_reports["Net Revenue"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
		},
		{
			fieldname: "case",
			label: __("Case"),
			fieldtype: "Select",
			options: ["", "Billed", "Non-Billed"],
		},
		{
			fieldname: "contract",
			label: __("Contract"),
			fieldtype: "Link",
			options: "CRM Contract",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "CRM Organization",
		},
		{
			fieldname: "region",
			label: __("Region"),
			fieldtype: "Link",
			options: "Region Master",
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Region Branches",
		},
	],

	tree: true,
	initial_depth: 1,

	onload() {
		// Row styling is keyed off marker classes the formatter puts in the cells, since the
		// datatable gives no per-row hook. Billed / Non-Billed rows show their totals only while
		// collapsed; once expanded the contract rows below carry the numbers. The datatable caches
		// formatted cells, so that is driven by the tree-close class it toggles on the label cell.
		$("#net-revenue-style").remove();
		$(`<style id="net-revenue-style">
			.dt-row:has(.nr-month) .dt-cell {
				background: var(--subtle-fg);
				border-top: 1px solid var(--border-color);
			}
			.dt-row:has(.nr-month) .dt-cell__content { font-weight: 600; }
			.dt-row:has(.nr-case--billed) .dt-cell { background: color-mix(in srgb, var(--bg-orange) 35%, transparent); }
			.dt-row:has(.nr-case--non-billed) .dt-cell { background: color-mix(in srgb, var(--bg-blue) 35%, transparent); }
			.dt-row:has(.nr-total) .dt-cell {
				background: var(--subtle-accent);
				border-top: 2px solid var(--gray-500);
				font-weight: 700;
			}
			.dt-row:not(:has(.dt-cell--tree-close)) .nr-case-total { visibility: hidden; }

			.nr-pill {
				display: inline-block;
				padding: 1px 8px;
				border-radius: 999px;
				font-size: var(--text-xs);
				font-weight: 600;
				line-height: 1.6;
			}
			.nr-pill--orange { background: var(--bg-orange); color: var(--text-on-orange); }
			.nr-pill--blue { background: var(--bg-blue); color: var(--text-on-blue); }
			.nr-pill--green { background: var(--bg-green); color: var(--text-on-green); }
			.nr-pill--yellow { background: var(--bg-yellow); color: var(--text-on-yellow); }
			.nr-pill--red { background: var(--bg-red); color: var(--text-on-red); }

			.nr-progress { display: flex; align-items: center; gap: 6px; justify-content: flex-end; }
			.nr-progress__bar {
				flex: 1;
				max-width: 44px;
				height: 6px;
				border-radius: 3px;
				background: var(--subtle-fg);
				overflow: hidden;
			}
			.nr-progress__fill { height: 100%; border-radius: 3px; }
			.nr-amount--due { color: var(--red-600); font-weight: 600; }
			.nr-amount--received { color: var(--green-600); }
		</style>`).appendTo("head");
	},

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		const field = column.fieldname;
		const pill = (color, text = value) => `<span class="nr-pill nr-pill--${color}">${text}</span>`;

		if (data.is_total) {
			return field === "label" ? `<span class="nr-total">${value}</span>` : value;
		}

		if (data.indent === 0) {
			return field === "label" ? `<span class="nr-month">${value}</span>` : value;
		}

		if (data.indent === 1) {
			const billed = data.label === "Billed";
			if (field === "label") {
				const marker = `nr-case--${billed ? "billed" : "non-billed"}`;
				return `<span class="${marker}">${pill(billed ? "orange" : "blue")}</span>`;
			}
			return `<span class="nr-case-total"><b>${value}</b></span>`;
		}

		switch (field) {
			case "pending_terms":
				return data.pending_terms > 1 ? pill("red") : value;
			case "days_overdue": {
				// Ageing buckets: 0-30 fine, 31-60 watch, 61-90 follow up, 90+ critical
				const days = data.days_overdue || 0;
				const bucket = days > 90 ? "red" : days > 60 ? "orange" : days > 30 ? "yellow" : "green";
				return pill(bucket, days);
			}
			case "collected_pct": {
				if (data.case !== "Billed") return value;
				const pct = Math.min(Math.max(data.collected_pct || 0, 0), 100);
				const c = pct >= 90 ? "green" : pct >= 50 ? "orange" : "red";
				return `<div class="nr-progress">
					<div class="nr-progress__bar">
						<div class="nr-progress__fill" style="width: ${pct}%; background: var(--${c}-500)"></div>
					</div>
					<span style="color: var(--${c}-600); font-weight: 600">${value}</span>
				</div>`;
			}
			case "received":
				return data.received > 0 ? `<span class="nr-amount--received">${value}</span>` : value;
			case "to_collect":
				return data.to_collect > 0 ? `<span class="nr-amount--due">${value}</span>` : value;
		}
		return value;
	},
};
