// Copyright (c) 2024, extension and contributors
// For license information, please see license.txt

// frappe.ui.form.on("CRM Contract", {
// 	refresh(frm) {

// 	},
// });


frappe.ui.form.on("CRM Contract", {
	refresh(frm) {
            set_payment_term_query(frm);
            console.log("script calling")
            frm.add_custom_button("Download Product Template", function () {

                let headers = [
                    "serial_no",
                    "product_name",
                    "product_group",
                    "custom_quantity",
                    "model_no",
                    "category_of_model",
                    "io",
                    "hp",
                    "ton",
                ];

                let csv_content = headers.join(",") + "\n";

                let blob = new Blob(
                    [csv_content],
                    { type: "text/csv;charset=utf-8;" }
                );

                let link = document.createElement("a");
                link.href = URL.createObjectURL(blob);
                link.download = "Product_Details_Template.csv";

                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

            }, "Product Details");

            frm.add_custom_button("Upload Product Template", function () {

                new frappe.ui.FileUploader({

                    allow_multiple: false,

                    on_success(file) {

                        console.log("Uploaded File:", file);

                        frappe.call({
                            method: "lg.lg.doctype.crm_contract.crm_contract.upload_product_details",

                            args: {
                                file_url: file.file_url,
                                docname: frm.doc.name
                            },

                            callback(r) {

                                if (!r.exc) {

                                    frappe.msgprint("Product Details Uploaded Successfully");

                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                });

            }, "Product Details");
		// console.log(`The Doctype name is : ${frm.doc.name}`);
		frm.add_web_link(`/app/customer/${frm.doc.name}`, __("Open in Portal"));

		// Add custom buttons only if document is saved
		if (!frm.doc.__islocal) {
			// if (frm.doc.expiry_date) {
			if (frm.doc.custom_contract_status == "Expired" || frm.doc.custom_contract_status == "Discontinue") {
				frappe.db.get_value("AMC Term", {"reference_contract": frm.doc.name}, "name", (r) => {
				if (r && r.name) {
					console.log("Already renewed: " + r.name);
				} else {
					// Agar koi record nahi mila, tabhi button show karein
					frm.add_custom_button(__("Renew"), function() {
						frappe.new_doc("AMC Term", {
							"customer": frm.doc.customer,
							"reference_contract": frm.doc.name
						});
					});
				}
			});
			}

			// Send Work Order: available on any saved, non-cancelled contract
			if (frm.doc.docstatus != 2) {
				frm.add_custom_button("Send Work Order", function () {

					frappe.call({
						method: "lg.lg.doctype.crm_contract.crm_contract.send_work_order",
						args: {
							name: frm.doc.name
						},
						freeze: true,
						freeze_message: __("Sending Work Order..."),

						callback: function (r) {
							console.log("r",r)
							if (!r.exc) {
								frappe.msgprint(__("Work Order sent successfully."));
							}
						}
					});

				});
			}

			// Add task list in activities tab
			if (frm.doc.name) {
				show_activity_list(frm);
			}
		}

	},
	
	expiry_date: function (frm) {
		set_status(frm)
		generate_billing_schedule(frm)
	},
	start_date: function (frm) {
		generate_billing_schedule(frm)
	},
	payment_frequency: function (frm) {
		generate_billing_schedule(frm)
	},
	payment_term: function (frm) {
		generate_billing_schedule(frm)
	},
	amount: function (frm) {
		generate_billing_schedule(frm)
	},
	billing_terms: async function (frm) {
		await clear_mismatched_payment_term(frm);
		generate_billing_schedule(frm)
	},

	validate: function(frm) {
        let total = 0;
        
        if (frm.doc.product_details) {
            frm.doc.product_details.forEach(row => {
                if (row.hp) {
                    total += flt(row.hp);
                }
            });
        }
        
        frm.set_value("total_hp", total);
    }



});


function set_status(frm) {
	const today = frappe.datetime.get_today();
	const expiry = frm.doc.expiry_date;

	if (expiry) {
		if (expiry < today) {
			frm.set_value("custom_contract_status", "Expired");
		} else {
			frm.set_value("custom_contract_status", "Active");
		}
	} else {
		frm.set_value("custom_contract_status", "Active");
	}
}




async function check_pending_activities(frm, doctype) {
	const response = await frappe.call({
		method: 'crm.fcrm.doctype.crm_contract.crm_contract.check_pending_activities',
		args: {
			deal: frm.doc.name,
			doctype: doctype
		}
	});
	return response.message;
}

function show_activity_list(frm) {
	const wrapper = frm.fields_dict.task_list.wrapper;
	wrapper.innerHTML = `
		<div class="activity-list">
			<div class="activity-filters margin-bottom">
				<div class="row">
					<div class="col-md-3">
						<select class="activity-type-filter form-control">
							<option value="all">All Activities</option>
							<option value="ToDo">Tasks</option>
							<option value="Event">Follow Ups</option>
						</select>
					</div>
					<div class="col-md-3">
						<select class="activity-status-filter form-control">
							<option value="all">All Status</option>
							<option value="Open">Open</option>
							<option value="Completed">Completed</option>
						</select>
					</div>
				</div>
			</div>
			<div class="activity-table-wrapper"></div>
		</div>
	`;

	// Add filter change handlers
	wrapper.querySelector('.activity-type-filter').addEventListener('change', function () {
		refresh_activity_list(frm);
	});
	wrapper.querySelector('.activity-status-filter').addEventListener('change', function () {
		refresh_activity_list(frm);
	});

	refresh_activity_list(frm);
}

function refresh_activity_list(frm) {
	const type_filter = frm.fields_dict.task_list.wrapper.querySelector('.activity-type-filter').value;
	const status_filter = frm.fields_dict.task_list.wrapper.querySelector('.activity-status-filter').value;

	// Convert 'all' to null for activity_type to show both types
	const activity_type = type_filter === 'all' ? null : type_filter;

	frappe.call({
		method: "crm.fcrm.doctype.crm_contract.crm_contract.get_deal_activities",
		args: {
			deal: frm.doc.name,
			activity_type: activity_type,
			status: status_filter
		},
		callback: function (r) {
			if (!r.exc) {
				render_activity_list(frm, r.message || []);
			}
		}
	});
}

function render_activity_list(frm, activities) {
	const wrapper = frm.fields_dict.task_list.wrapper.querySelector('.activity-table-wrapper');

	let html = `<div class="table-responsive">
		<table class="table table-bordered">
			<thead>
				<tr>
					<th>Type</th>
					<th>Description</th>
					<th>Status</th>
					<th>Due Date</th>
					<th>Assigned To</th>
					<th>Actions</th>
				</tr>
			</thead>
			<tbody>`;

	if (activities.length) {
		activities.forEach(activity => {
			html += `<tr>
				<td>${activity.activity_type}</td>
				<td>${activity.description || ''}</td>
				<td>${activity.status}</td>
				<td>${activity.date ? frappe.datetime.str_to_user(activity.date) : ''}</td>
				<td>${activity.allocated_to || ''}</td>
				<td>`;

			if (activity.status === "Open") {
				html += `<button class="btn btn-xs btn-complete-activity" 
					data-type="${activity.activity_type}"
					data-id="${activity.name}">Complete</button>`;
			}

			html += `</td></tr>`;
		});
	} else {
		html += `<tr><td colspan="6" class="text-center">No activities found</td></tr>`;
	}

	html += `</tbody></table></div>`;

	wrapper.innerHTML = html;

	// Add handlers
	wrapper.querySelectorAll('.btn-complete-activity').forEach(btn => {
		btn.addEventListener('click', function () {
			const type = this.dataset.type;
			const id = this.dataset.id;
			show_complete_activity_dialog(frm, type, id);
		});
	});

	// Add styles
	if (!document.getElementById('activity-list-styles')) {
		const style = document.createElement('style');
		style.id = 'activity-list-styles';
		style.textContent = `
			.activity-list {
				padding: 15px;
			}
			.activity-filters {
				margin-bottom: 15px;
			}
			.activity-filters .row {
				margin: 0 -8px;
			}
			.activity-filters .col-md-3 {
				padding: 0 8px;
			}
			.table-responsive {
				border-radius: 8px;
				overflow: hidden;
				box-shadow: 0 1px 3px rgba(0,0,0,0.1);
			}
			.table thead th {
				background-color: var(--fg-color);
				font-weight: 600;
			}
			.table td, .table th {
				padding: 0.75rem;
				vertical-align: middle;
			}
			.btn-complete-activity {
				background-color: var(--primary);
				color: white;
				border: none;
				padding: 4px 8px;
				border-radius: 4px;
			}
			.btn-complete-activity:hover {
				background-color: var(--primary-dark);
			}
		`;
		document.head.appendChild(style);
	}
}

function show_task_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __('Create Task'),
		fields: [
			{
				fieldname: 'description',
				label: __('Description'),
				fieldtype: 'Small Text',
				reqd: 1
			},
			{
				fieldname: 'date',
				label: __('Due Date'),
				fieldtype: 'Datetime',
				reqd: 1
			},
			{
				fieldname: 'assigned_to',
				label: __('Assign To'),
				fieldtype: 'Link',
				options: 'User',
				reqd: 1,
				default: frappe.session.user
			}
		],
		primary_action_label: __('Create'),
		primary_action(values) {
			frappe.call({
				method: 'crm.fcrm.doctype.crm_contract.crm_contract.create_deal_task',
				args: {
					deal: frm.doc.name,
					description: values.description,
					date: values.date,
					assigned_to: values.assigned_to
				},
				callback: function (r) {
					if (!r.exc) {
						d.hide();
						refresh_activity_list(frm);
						frappe.show_alert({
							message: __('Task created'),
							indicator: 'green'
						});
					}
				}
			});
		}
	});
	d.show();
}

function show_follow_up_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __('Create Follow Up'),
		fields: [
			{
				fieldname: 'subject',
				label: __('Subject'),
				fieldtype: 'Data',
				reqd: 1
			},
			{
				fieldname: 'type',
				label: __('Type'),
				fieldtype: 'Select',
				options: ['Meeting', 'Call', 'Email'],
				reqd: 1
			},
			{
				fieldname: 'description',
				label: __('Description'),
				fieldtype: 'Small Text',
				reqd: 1
			},
			{
				fieldname: 'date',
				label: __('Date & Time'),
				fieldtype: 'Datetime',
				reqd: 1
			},
			{
				fieldname: 'assigned_to',
				label: __('Assign To'),
				fieldtype: 'Link',
				options: 'User',
				reqd: 1,
				default: frappe.session.user
			}
		],
		primary_action_label: __('Create'),
		primary_action(values) {
			frappe.call({
				method: 'crm.fcrm.doctype.crm_contract.crm_contract.create_follow_up',
				args: {
					deal: frm.doc.name,
					subject: values.subject,
					type: values.type,
					description: values.description,
					date: values.date,
					assigned_to: values.assigned_to
				},
				callback: function (r) {
					if (!r.exc) {
						d.hide();
						refresh_activity_list(frm);
						frappe.show_alert({
							message: __('Follow up created'),
							indicator: 'green'
						});
					}
				}
			});
		}
	});
	d.show();
}

function show_complete_activity_dialog(frm, type, id) {
	const d = new frappe.ui.Dialog({
		title: __(`Complete ${type}`),
		fields: [
			{
				fieldname: 'completion_note',
				label: __('Completion Note'),
				fieldtype: 'Small Text',
				reqd: 1,
				description: __('Please provide details about the completion of this activity')
			}
		],
		primary_action_label: __('Complete'),
		primary_action(values) {
			frappe.call({
				method: 'crm.fcrm.doctype.crm_contract.crm_contract.complete_activity',
				args: {
					activity_type: type,
					activity_id: id,
					completion_note: values.completion_note
				},
				callback: function (r) {
					if (!r.exc) {
						d.hide();
						refresh_activity_list(frm);
						frappe.show_alert({
							message: __(`${type} completed`),
							indicator: 'green'
						});
					}
				}
			});
		}
	});
	d.show();
}



frappe.ui.form.on('Contract Billing Schedule', {
	upload: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!row.upload) return;

		frappe.call({
			method: "lg.lg.doctype.crm_contract.crm_contract.process_billing_excel",
			args: { file_url: row.upload },
			callback: function (r) {
				console.log("response", r)
				if (!r.exc && r.message) {
					// r.message is a list of rows
					r.message.forEach((item, index) => {
						// Add new row in child table if needed
						let child = frm.add_child('billing_schedule');
						frappe.model.set_value(child.doctype, child.name, 'invoice_id', item['Invoice ID']);
						frappe.model.set_value(child.doctype, child.name, 'amount_received', item['Amount']);
						frappe.model.set_value(child.Doctype, child.name, 'status', 'Paid')
					});
					frm.refresh_field('billing_schedule');
					frappe.msgprint(__('Invoice data updated from Excel'));
				}
			},
			error: function (err) {
				console.error("Server Error:", err);
			}
		});
	}
});




// ============================================================================
// Billing schedule auto-generation (same behaviour as CRM Quotation)
// ============================================================================

// Only Pay Terms matching the Payment Frequency (billing_terms: Advance/Post) can be picked
function set_payment_term_query(frm) {
	frm.set_query("payment_term", () => {
		if (frm.doc.billing_terms) {
			return { filters: { payment_frequency: frm.doc.billing_terms } };
		}
		return {};
	});
}

async function clear_mismatched_payment_term(frm) {
	if (!frm.doc.billing_terms || !frm.doc.payment_term) return;
	const { message } = await frappe.db.get_value("Pay Term", frm.doc.payment_term, "payment_frequency");
	if (message && message.payment_frequency !== frm.doc.billing_terms) {
		await frm.set_value("payment_term", "");
	}
}

function get_ordinal(n) {
	const s = ["th", "st", "nd", "rd"], v = n % 100;
	return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

async function generate_billing_schedule(frm) {
	const { start_date, expiry_date, payment_frequency, payment_term, amount: total_amount } = frm.doc;
	const billing_terms = frm.doc.billing_terms || "Post";

	if (!start_date || !expiry_date || !payment_frequency || !total_amount) return;

	// never overwrite a schedule that is already being billed / paid
	if (frm.doc.docstatus === 1) return;
	if ((frm.doc.billing_schedule || []).some(r => (r.status && r.status !== "Pending") || r.invoice_id || r.invoice_link)) return;

	// min days / portion from the Pay Term
	let min_days = 0;
	let min_invoice_portion = 100;
	if (payment_term) {
		const doc = await frappe.db.get_doc("Pay Term", payment_term);
		if (doc && doc.payment_term_portions?.length > 0) {
			const min_row = doc.payment_term_portions.reduce((prev, curr) =>
				(curr.days || 0) < (prev.days || 0) ? curr : prev);
			min_days = min_row.days || 0;
			min_invoice_portion = min_row.invoice_portion || 100;
		}
	}

	const add_row = (billing_date, amount, term, portion) => {
		const row = frm.add_child("billing_schedule");
		row.billing_date = frappe.datetime.obj_to_str(billing_date);
		const pay = new Date(billing_date.getTime());
		pay.setDate(pay.getDate() + min_days);
		row.payment_date = frappe.datetime.obj_to_str(pay);
		row.amount = amount;
		row.billing_term = term;
		row.status = "Pending";
		row.invoice_portion = portion;
	};

	frm.clear_table("billing_schedule");

	if (payment_frequency === "100% for Partial Contract") {
		const d = frappe.datetime.str_to_obj(billing_terms === "Advance" ? start_date : expiry_date);
		add_row(d, flt(total_amount), "Full Payment", 100);
		frm.refresh_field("billing_schedule");
		return;
	}

	const months_to_add = { "Monthly": 1, "Quarterly": 3, "Semi-Annually": 6, "Annually": 12 }[payment_frequency];
	if (!months_to_add) return;

	const end_obj = frappe.datetime.str_to_obj(expiry_date);
	const dates = [];
	if (billing_terms === "Advance") dates.push(frappe.datetime.str_to_obj(start_date));

	let current = frappe.datetime.str_to_obj(start_date);
	while (true) {
		const next = new Date(current.getTime());
		next.setMonth(next.getMonth() + months_to_add);
		if (next > end_obj) {
			dates.push(end_obj);
			break;
		}
		dates.push(next);
		current = next;
	}
	// remove duplicate end date in Advance case
	if (billing_terms === "Advance" && dates.length > 1) dates.pop();

	// equal split; the last row absorbs the rounding difference
	const each = flt(flt(total_amount) / dates.length, 2);
	dates.forEach((d, i) => {
		const amt = i === dates.length - 1 ? flt(flt(total_amount) - each * (dates.length - 1), 2) : each;
		add_row(d, amt, get_ordinal(i + 1) + " Term", min_invoice_portion);
	});

	frm.refresh_field("billing_schedule");
}
