// Copyright (c) 2024, extension and contributors
// For license information, please see license.txt

// frappe.ui.form.on("CRM Contract", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("CRM Contract", {
	refresh(frm) {
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
			


			// Add task list in activities tab
			if (frm.doc.name) {
				show_activity_list(frm);
			}
		}
	},
	
	expiry_date: function (frm) {
		set_status(frm)
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


