// Copyright (c) 2024, extension and contributors
// For license information, please see license.txt
let auto_price_rate = false;

frappe.ui.form.on("CRM Quotation", {
    refresh(frm) {

        set_default_print_format(frm);
        frm.set_df_property("total_hp", "read_only", 1);
        if (frm.doc.total_hp && frm.doc.industry) {
            show_filtered_zone_rates(frm);
        }

        frm.add_custom_button(__('Send Email'), function () {
            // Open the same Email dialog
            new frappe.views.CommunicationComposer({
                doc: frm.doc,
                frm: frm,
                subject: __("Quotation: {0}", [frm.doc.name]),
                recipients: frm.doc.contact_email || "",   // customer email field
                sender: "econnect.himsolutek@lgepartner.com",
                attach_document_print: true,  // attach PDF
                message: __("Please find attached quotation."),
            });
        });

        // Add custom button only if document is submitted
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Create Sub Contract'), function () {
                frappe.model.open_mapped_doc({
                    method: "crm.fcrm.doctype.crm_quotation.crm_quotation.make_crm_contract",
                    frm: frm
                });
            });
        }

        // Add the attachment functionality
        if (frm.doc.__islocal) return;
        const wrapper = $(frm.fields_dict["attachments"].wrapper);
        wrapper.empty();


        wrapper.append(`
                <div>
                    <button class="btn btn-sm btn-primary" id="upload-pdf-btn">Upload PDF</button>
                    <div id="pdf-tabs" class="mt-3 nav nav-tabs"></div>
                    <div id="pdf-preview" class="mt-3" style="border: 1px solid #ccc; height: 400px;"></div>
                </div>
                `);

        const renderPreview = (file_url) => {
            $('#pdf-preview').html(`
                <p><a href="${file_url}" class="link-primary">Open In New Tab</a></p>
                <embed src="${file_url}" width="100%" height="100%" type="application/pdf">
            `);
        };

        const renderTabs = (files) => {
            const $tabs = $('#pdf-tabs');
            $tabs.empty();

            files.forEach((file, index) => {
                const tabId = `tab-${index}`;
                const activeClass = index === 0 ? 'active' : '';
                $tabs.append(`
                    <a class="nav-link ${activeClass}" data-url="${file.file_url}" data-tab-id="${tabId}" href="#">${file.file_name}</a>
                `);
            });

            // Initial preview
            if (files.length > 0) {
                renderPreview(files[0].file_url);
            }

            // Tab click handler
            $tabs.find('a').on('click', function (e) {
                e.preventDefault();
                $tabs.find('a').removeClass('active');
                $(this).addClass('active');

                const url = $(this).data('url');
                renderPreview(url);
            });
        };

        const fetchAndRenderFiles = () => {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'File',
                    filters: {
                        attached_to_doctype: frm.doctype,
                        attached_to_name: frm.doc.name,
                        is_folder: 0,
                    },
                    fields: ['file_url', 'file_name'],
                    limit_page_length: 100
                },
                callback: function (r) {
                    renderTabs(r.message || []);
                }
            });
        };

        const updateTheStatus = () => {
            const statusNeedsUpdate = frm.doc.status !== "PO Received";
            const workflowNeedsUpdate = frm.doc.workflow_state !== "PO Received";

            if (statusNeedsUpdate || workflowNeedsUpdate) {
                frm.set_value("uploaded", 1);
                frm.save();
            }
        };


        // Attach upload button handler
        $('#upload-pdf-btn').on('click', function () {
            new frappe.ui.FileUploader({
                allow_multiple: true,
                doctype: frm.doctype,
                docname: frm.doc.name,

                on_success: () => {
                    updateTheStatus();
                    fetchAndRenderFiles()
                }
            });
        });

        fetchAndRenderFiles(); // Initial load

    },
    // Workflow validation
    before_workflow_action(frm, workflow_action) {
        if (frm.doc.workflow_state === "PO Pending") {

            let uploaded = frm.doc.uploaded;
            if (!uploaded) {
                setTimeout(() => {
                    frappe.dom.unfreeze();
                }, 2000)
                frappe.throw(__('Please upload at least one PDF attachment before proceeding.'));
            }
        }

        // Map each workflow state to its remarks field and display name
        const remarksMapping = {
            "Approval Pending": {
                field: "remarks",
                label: "Approval"
            },
            "Yellow Zone Approval Pending": {
                field: "yellow_zone_approve_rejection_remarks",
                label: "Yellow Zone"
            },
            "Orange Zone Approval Pending": {
                field: "orange_zone_approve_rejection_remarks",
                label: "Orange Zone"
            },
            "Red Zone Approval Pending": {
                field: "red_zone_approve_rejection_remarks",
                label: "Red Zone"
            }
        };

        let current = remarksMapping[frm.doc.workflow_state];
        if (current && !frm.doc[current.field]) {
            setTimeout(() => {
                frappe.dom.unfreeze();
            }, 1000);
            frappe.throw(__("Please enter remarks for {0} before proceeding.", [current.label]));
        }
    },


    start_date: function (frm) {
        generate_billing_schedule(frm)
        calculate_amc_duration(frm);

    },
    end_date: function (frm) {
        generate_billing_schedule(frm)
        calculate_amc_duration(frm);

    },
    payment_term: function (frm) {
        generate_billing_schedule(frm)
        calculate_amc_duration(frm);

    },

    payment_frequency: function (frm) {
        generate_billing_schedule(frm)
    },
    industry(frm) {
        if (frm.doc.total_hp) {
            show_filtered_zone_rates(frm);
        }
    },
    billing_terms: function (frm) {
        generate_billing_schedule(frm)
    },

    date(frm) {
        update_valid_till(frm);
    },

    zone(frm) {
        fetch_price_rate_from_zone(frm);
    },
    price_rate: function (frm) {
        calculate_amount(frm)
        fetch_zone_from_price_rate(frm);

    },
    total_hp: function (frm) {
        calculate_amount(frm)
    },
    total_tonne: function (frm) {
        calculate_total_ton_amount(frm)
    },
    price_rate_as_per_ton: function (frm) {
        calculate_total_ton_amount(frm)
    },
    amc_year: function (frm) {
        calculate_amount(frm)
        detect_multi_year(frm)
    },
    amc_term: function (frm) {
        detect_multi_year(frm)
    },
    start_date_as_per_po: function (frm) {
        generate_billing_schedule_as_per_po_date(frm)
    },
    end_date_as_per_po: function (frm) {
        generate_billing_schedule_as_per_po_date(frm)
    }


});


function calculate_total_ton_amount(frm) {
    const total_ton = frm.doc.total_tonne
    const priceRate_ton = frm.doc.price_rate_as_per_ton
    const amcYear = frm.doc.amc_year
    let res = total_ton * priceRate_ton * amcYear
    frm.set_value('total_as_ton_inr', res)


}

async function generate_billing_schedule(frm) {
    const {
        start_date,
        end_date,
        payment_frequency,
        payment_term,
        amount: total_amount,
    } = frm.doc;

    const billing_terms = frm.doc.billing_terms || "Post"; // Pre or Post or Advance

    if (!start_date || !end_date || !payment_frequency || !total_amount) {
        return;
    }

    frm.clear_table("billing_schedule");

    // =====================================================
    // 🔹 Special Case: 100% (Partial Contract)
    // =====================================================
    if (payment_frequency === "100% for Partial Contract") {

        let billing_date = (billing_terms === "Advance")
            ? frappe.datetime.str_to_obj(start_date)
            : frappe.datetime.str_to_obj(end_date);

        // 🔹 Get minimum days row from Payment Term
        let min_row = null;
        if (payment_term) {
            await frappe.db.get_doc("Pay Term", payment_term).then(doc => {
                if (doc && doc.payment_term_portions?.length > 0) {
                    min_row = doc.payment_term_portions.reduce((prev, curr) => {
                        return (curr.days || 0) < (prev.days || 0) ? curr : prev;
                    });
                }
            });
        }

        let min_days = min_row ? min_row.days : 0;

        const row = frm.add_child("billing_schedule");
        row.billing_date = frappe.datetime.obj_to_str(billing_date);

        let payment_date_obj = new Date(billing_date.getTime());
        payment_date_obj.setDate(payment_date_obj.getDate() + min_days);
        row.payment_date = frappe.datetime.obj_to_str(payment_date_obj);

        row.amount = flt(total_amount);
        row.billing_term = "Full Payment";
        row.status = "Pending";
        row.invoice_portion = 100;

        frm.refresh_field("billing_schedule");
        return;
    }

    // =====================================================
    // 🔹 Normal Frequency Logic
    // =====================================================

    const freq_map = {
        "Monthly": 1,
        "Quarterly": 3,
        "Semi-Annually": 6,
        "Annually": 12
    };

    const months_to_add = freq_map[payment_frequency];
    if (!months_to_add) return;

    let term_counter = 1;
    let end_obj = frappe.datetime.str_to_obj(end_date);
    let dates = [];

    // 🔹 If billing_terms is Advance, start with start_date
    if (billing_terms === "Advance") {
        dates.push(frappe.datetime.str_to_obj(start_date));
    }

    let current = frappe.datetime.str_to_obj(start_date);

    while (true) {
        let next = new Date(current.getTime());
        next.setMonth(next.getMonth() + months_to_add);

        if (next > end_obj) {
            dates.push(end_obj);
            break;
        } else {
            dates.push(next);
            current = next;
        }
    }

    // 🔹 Remove duplicate end date in Advance case
    if (billing_terms === "Advance" && dates.length > 1) {
        dates.pop();
    }

    const per_row_amount = dates.length > 0 ? flt(total_amount) / dates.length : 0;

    // 🔹 Get minimum days row from Payment Term
    let min_row = null;
    if (payment_term) {
        await frappe.db.get_doc("Pay Term", payment_term).then(doc => {
            if (doc && doc.payment_term_portions?.length > 0) {
                min_row = doc.payment_term_portions.reduce((prev, curr) => {
                    return (curr.days || 0) < (prev.days || 0) ? curr : prev;
                });
            }
        });
    }

    let min_days = min_row ? min_row.days : 0;
    let min_invoice_portion = min_row ? min_row.invoice_portion : 100;

    for (let i = 0; i < dates.length; i++) {
        const row = frm.add_child("billing_schedule");
        row.billing_date = frappe.datetime.obj_to_str(dates[i]);

        let billing_date_obj = new Date(dates[i].getTime());
        billing_date_obj.setDate(billing_date_obj.getDate() + min_days);
        row.payment_date = frappe.datetime.obj_to_str(billing_date_obj);

        row.amount = per_row_amount;
        row.billing_term = get_ordinal(term_counter++) + " Term";
        row.status = "Pending";
        row.invoice_portion = min_invoice_portion;
    }

    frm.refresh_field("billing_schedule");
}

function get_ordinal(n) {
    const s = ["th", "st", "nd", "rd"], v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
}


async function generate_billing_schedule_as_per_po_date(frm) {
    console.log("Starting generate_billing_schedule_as_per_po_date...");
    
    const {
        start_date_as_per_po,
        end_date_as_per_po,
        payment_frequency,
        payment_term,
        amount: total_amount,
    } = frm.doc;

    const billing_terms = frm.doc.billing_terms || "Post"; 
    
    console.log("Input Values:", {
        start_date_as_per_po,
        end_date_as_per_po,
        payment_frequency,
        payment_term,
        total_amount,
        billing_terms
    });

    if (!end_date_as_per_po || !start_date_as_per_po || !payment_frequency || !total_amount) {
        console.warn("Missing required fields. Execution stopped.");
        return;
    }

    frm.clear_table("billing_schedule");

    // =====================================================
    // 🔹 Special Case: 100% (Partial Contract)
    // =====================================================
    if (payment_frequency === "100% for Partial Contract") {
        console.log("Logic: 100% for Partial Contract detected.");

        let billing_date = (billing_terms === "Advance")
            ? frappe.datetime.str_to_obj(start_date_as_per_po)
            : frappe.datetime.str_to_obj(end_date_as_per_po);

        let min_days = 0;
        if (payment_term) {
            await frappe.db.get_doc("Pay Term", payment_term).then(doc => {
                if (doc && doc.payment_term_portions?.length > 0) {
                    let min_row = doc.payment_term_portions.reduce((prev, curr) => {
                        return (curr.days || 0) < (prev.days || 0) ? curr : prev;
                    });
                    min_days = min_row ? min_row.days : 0;
                    console.log("Fetched min_days from Pay Term:", min_days);
                }
            });
        }

        const row = frm.add_child("billing_schedule");
        row.billing_date = frappe.datetime.obj_to_str(billing_date);

        let payment_date_obj = new Date(billing_date.getTime());
        payment_date_obj.setDate(payment_date_obj.getDate() + min_days);
        row.payment_date = frappe.datetime.obj_to_str(payment_date_obj);

        row.amount = flt(total_amount);
        row.billing_term = "Full Payment";
        row.status = "Pending";
        row.invoice_portion = 100;

        console.log("Row added for 100% Partial Contract:", row);
        frm.refresh_field("billing_schedule");
        return;
    }

    // =====================================================
    // 🔹 Normal Frequency Logic
    // =====================================================
    const freq_map = {
        "Monthly": 1,
        "Quarterly": 3,
        "Semi-Annually": 6,
        "Annually": 12
    };

    const months_to_add = freq_map[payment_frequency];
    console.log("Months to add based on frequency:", months_to_add);
    
    if (!months_to_add) {
        console.error("Invalid frequency mapping.");
        return;
    }

    let term_counter = 1;
    let end_obj = frappe.datetime.str_to_obj(end_date_as_per_po);
    let dates = [];

    if (billing_terms === "Advance") {
        dates.push(frappe.datetime.str_to_obj(start_date_as_per_po));
    }

    let current = frappe.datetime.str_to_obj(start_date_as_per_po);

    while (true) {
        let next = new Date(current.getTime());
        next.setMonth(next.getMonth() + months_to_add);

        if (next > end_obj) {
            dates.push(end_obj);
            break;
        } else {
            dates.push(next);
            current = next;
        }
    }

    if (billing_terms === "Advance" && dates.length > 1) {
        dates.pop();
    }

    console.log("Calculated schedule dates:", dates);

    const per_row_amount = dates.length > 0 ? flt(total_amount) / dates.length : 0;
    console.log("Calculated per-row amount:", per_row_amount);

    let min_days = 0;
    let min_invoice_portion = 100;

    if (payment_term) {
        await frappe.db.get_doc("Pay Term", payment_term).then(doc => {
            if (doc && doc.payment_term_portions?.length > 0) {
                let min_row = doc.payment_term_portions.reduce((prev, curr) => {
                    return (curr.days || 0) < (prev.days || 0) ? curr : prev;
                });
                min_days = min_row ? min_row.days : 0;
                min_invoice_portion = min_row ? min_row.invoice_portion : 100;
                console.log("Fetched Pay Term values:", { min_days, min_invoice_portion });
            }
        });
    }

    for (let i = 0; i < dates.length; i++) {
        const row = frm.add_child("billing_schedule");
        row.billing_date = frappe.datetime.obj_to_str(dates[i]);

        let billing_date_obj = new Date(dates[i].getTime());
        billing_date_obj.setDate(billing_date_obj.getDate() + min_days);
        row.payment_date = frappe.datetime.obj_to_str(billing_date_obj);

        row.amount = per_row_amount;
        row.billing_term = get_ordinal(term_counter++) + " Term";
        row.status = "Pending";
        row.invoice_portion = min_invoice_portion;
        
        console.log(`Added row ${i+1}:`, row);
    }

    frm.refresh_field("billing_schedule");
    console.log("Billing schedule generation complete.");
}

function get_ordinal(n) {
    const s = ["th", "st", "nd", "rd"], v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
}






function fetch_price_rate_from_zone(frm) {
    if (!frm.doc.zone) return;

    // Get HTML inside zone_rates field
    let $wrapper = frm.fields_dict.zone_rates.$wrapper;

    let $rows = $wrapper.find("tbody tr");

    let found = false;
    let rate = 0;

    $rows.each(function (idx) {
        let $cells = $(this).find("td");

        if ($cells.length >= 4) {
            let zone_name = $cells.eq(3).text().trim();   // 4th col = Zone
            if (zone_name === frm.doc.zone) {
                rate = parseFloat($cells.eq(2).text().trim()) || 0;  // 3rd col = Max Rate
                found = true;
                return false; // stop looping once match is found
            }
        }
    });

    // if (found && rate > 0) {
    //     frm.set_value("price_rate", rate);
    // } else {
    //     frm.set_value("price_rate", 0);
    // }
}





function calculate_amount(frm) {
    const total_hp = frm.doc.total_hp
    const priceRate = frm.doc.price_rate
    const amcYear = frm.doc.amc_year
    let res = total_hp * priceRate * amcYear
    frm.set_value('amount', res)
}



frappe.ui.form.on('Product Details', {
    hp(frm, cdt, cdn) {
        calculate_total_total_hp_for_quotation(frm);
        if (frm.doc.industry) {
            show_filtered_zone_rates(frm);
        }
    },
    tonnes(frm, cdt, cdn) {
        calculate_total_ton_hp_for_quotation(frm);
    }
});

function calculate_total_total_hp_for_quotation(frm) {
    let total = 0;
    (frm.doc.product_details || []).forEach(row => {
        const val = parseFloat(row.hp);
        if (!isNaN(val)) total += val;
    });
    auto_price_rate = true;
    frm.set_value("total_hp", total);

    priceRate(frm);
    if (frm.doc.industry) {
        show_filtered_zone_rates(frm);
    }
}

function calculate_total_ton_hp_for_quotation(frm) {
    let total = 0;
    (frm.doc.product_details || []).forEach(row => {
        const val = parseFloat(row.tonnes);
        if (!isNaN(val)) total += val;
    });
    auto_price_rate = true;
    frm.set_value("total_tonne", total);

}


function update_valid_till(frm) {
    if (frm.doc.date) {
        const valid_till = frappe.datetime.add_days(frm.doc.date, 15);
        frm.set_value('valid_till', valid_till)
    }
}

function priceRate(frm) {
    if (!frm.doc.industry || !frm.doc.total_hp) return;
    if (!auto_price_rate && frm.doc.price_rate) return;

    frappe.call({
        method: "lg.lg.doctype.crm_quotation.crm_quotation.get_zone_from_vertical_master",
        args: {
            horse_power: frm.doc.total_hp,
            project_type: frm.doc.industry,
            start_date: frm.doc.start_date,
            end_date: frm.doc.end_date,
            price_rate: frm.doc.price_rate || null
        },
        callback: function (r) {
            if (r.message) {
                if (r.message.error) return;

                frm.set_value("zone", r.message.zone || "");
                let rate = parseFloat(r.message.price_rate) || 0;
                let min_rate = parseFloat(r.message.minimum_rate || 0);
                let max_rate = parseFloat(r.message.maximum_rate || 0);
                let manual_rate = parseFloat(frm.doc.price_rate || 0);

                if (!frm.doc.price_rate || frm.doc.price_rate == 0) {
                    frm.set_value("price_rate", rate);
                    frm.set_value("amount", rate);
                } else {
                    if (manual_rate >= min_rate && manual_rate <= max_rate) {
                        frm.set_value("amount", manual_rate);
                    } else {
                        frm.set_value("price_rate", rate);
                        frm.set_value("amount", rate);
                    }
                }

                set_amc_values(frm, r.message.amc_year || 0, r.message.amc_term || 0);
                auto_price_rate = false;
            }
        }
    });
}



// function fetch_zone_from_price_rate(frm) {
//     if (!frm.doc.industry || !frm.doc.total_hp || !frm.doc.price_rate) return;

//     // 🔹 Step 1: First fetch CRM Industry to get parent_vertical
//     frappe.db.get_list('CRM Industry', {
//         filters: { name: frm.doc.industry },
//         fields: ['parent_vertical'],
//         limit: 1
//     }).then(indRes => {
//         if (!indRes.length || !indRes[0].parent_vertical) return;

//         let parent_vertical = indRes[0].parent_vertical;

//         // 🔹 Step 2: Now check if Vertical Master exists with this parent_vertical
//         frappe.db.get_list('Vertical Master', {
//             filters: { name: parent_vertical },
//             fields: ['name'],
//             limit: 1
//         }).then(res => {
//             if (!res.length) return;

//             // 🔹 Step 3: Fetch Vertical Master doc
//             frappe.db.get_doc('Vertical Master', res[0].name).then(doc => {
//                 let total_hp = parseFloat(frm.doc.total_hp);
//                 let rate = parseFloat(frm.doc.price_rate);
//                 let matched_zone = "";

//                 (doc.hp_and_zone_details || []).forEach(row => {
//                     let range = row.hp?.replace("HP", "").trim();
//                     let matched = false;

//                     try {
//                         if (range.includes("~")) {
//                             const [min, max] = range.split("~").map(p => parseFloat(p.trim()));
//                             if (total_hp >= min && total_hp <= max) matched = true;
//                         } else {
//                             const total_hp_val = parseFloat(range);
//                             if (total_hp === total_hp_val) matched = true;
//                         }

//                         let min_rate = parseFloat(row.minimum_rate) || 0;
//                         let max_rate = parseFloat(row.maximum_rate) || 0;

//                         if (matched && rate >= min_rate && rate <= max_rate) {
//                             matched_zone = row.zone;
//                         }
//                     } catch (e) {
//                         console.warn("HP parse error", e);
//                     }
//                 });

//                 frm.set_value("zone", matched_zone || "");
//             });
//         });
//     });
// }
async function fetch_zone_from_price_rate(frm) {

    if (!frm.doc.industry || !frm.doc.total_hp || !frm.doc.price_rate) return;

    try {

        // Step 1: CRM Industry
        let indRes = await frappe.db.get_list('CRM Industry', {
            filters: { name: frm.doc.industry },
            fields: ['parent_vertical'],
            limit: 1
        });

        if (!indRes.length || !indRes[0].parent_vertical) return;

        let parent_vertical = indRes[0].parent_vertical;

        // Step 2: Vertical Master
        let vmRes = await frappe.db.get_list('Vertical Master', {
            filters: { name: parent_vertical },
            fields: ['name'],
            limit: 1
        });

        if (!vmRes.length) return;

        let doc = await frappe.db.get_doc('Vertical Master', vmRes[0].name);

        let total_hp = parseFloat(frm.doc.total_hp);
        let rate = parseFloat(frm.doc.price_rate);

        let matched_zone = "";

        let rows = doc.hp_and_zone_details || [];

        let lowestRow = null;
        let highestRow = null;
        let lowestRate = Infinity;
        let highestRate = -Infinity;

        for (let row of rows) {

            let range = row.hp?.replace("HP", "").trim();
            if (!range) continue;

            let minVal, maxVal;

            if (range.includes("~")) {
                [minVal, maxVal] = range.split("~").map(p => parseFloat(p.trim()));
            } else {
                minVal = maxVal = parseFloat(range);
            }

            let hpMatched = total_hp >= minVal && total_hp <= maxVal;

            let min_rate = parseFloat(row.minimum_rate) || 0;
            let max_rate = parseFloat(row.maximum_rate) || 0;

            // track lowest & highest rate rows
            if (min_rate < lowestRate) {
                lowestRate = min_rate;
                lowestRow = row;
            }

            if (max_rate > highestRate) {
                highestRate = max_rate;
                highestRow = row;
            }

            if (hpMatched && rate >= min_rate && rate <= max_rate) {
                matched_zone = row.zone;
            }
        }

        // fallback logic
        if (!matched_zone) {

            if (rate > highestRate && highestRow) {
                matched_zone = highestRow.zone;   // Green assumed
            }

            else if (rate < lowestRate && lowestRow) {
                matched_zone = lowestRow.zone;   // Red assumed
            }
        }

        frm.set_value("zone", matched_zone || "");

    } catch (error) {
        console.error("Zone Fetch Error:", error);
        frappe.msgprint("Error while calculating zone.");
    }
}


function show_filtered_zone_rates(frm) {
    if (!frm.doc.industry || !frm.doc.total_hp) return;

    // Step 1: Get CRM Industry record
    frappe.db.get_list('CRM Industry', {
        filters: { name: frm.doc.industry },
        fields: ['parent_vertical'],
        limit: 1
    }).then(indRes => {
        if (!indRes.length || !indRes[0].parent_vertical) return;

        let parent_vertical = indRes[0].parent_vertical;

        // Step 2: Get Vertical Master record using parent_vertical
        frappe.db.get_list('Vertical Master', {
            filters: { name1: parent_vertical },
            fields: ['name'],
            limit: 1
        }).then(vmRes => {
            if (!vmRes.length) return;

            // Step 3: Fetch full Vertical Master doc
            frappe.db.get_doc('Vertical Master', vmRes[0].name).then(doc => {
                let entered_total_hp = parseFloat(frm.doc.total_hp);
                let html = `<table class="table table-bordered" style="margin-top:10px;">
                    <thead>
                        <tr>
                            <th>HP</th>
                            <th>Minimum Rate</th>
                            <th>Maximum Rate</th>
                            <th>Zone</th>
                        </tr>
                    </thead>
                    <tbody>`;

                let matched = false;

                (doc.hp_and_zone_details || []).forEach(row => {
                    let range = row.hp?.replace("HP", "").trim();
                    let min_rate = row.minimum_rate ?? "";
                    let max_rate = row.maximum_rate ?? "";
                    let zone = row.zone || "";

                    let match = false;
                    try {
                        if (range.includes("~")) {
                            const [min, max] = range.split("~").map(p => parseFloat(p.trim()));
                            if (entered_total_hp >= min && entered_total_hp <= max) match = true;
                        } else {
                            const total_hp_val = parseFloat(range);
                            if (entered_total_hp === total_hp_val) match = true;
                        }
                    } catch (e) { }

                    if (match) {
                        matched = true;
                        html += `<tr>
                            <td>${row.hp}</td>
                            <td>${min_rate}</td>
                            <td>${max_rate}</td>
                            <td>${zone}</td>
                        </tr>`;
                    }
                });

                if (!matched) {
                    html += `<tr><td colspan="4" style="text-align:center;">No matching zone rates found</td></tr>`;
                }

                html += `</tbody></table>`;

                // Step 4: Set table in field
                frm.set_df_property("zone_rates", "options", html);
                fetch_price_rate_from_zone(frm)
                frm.refresh_field("zone_rates");
            });
        });
    });
}


function calculate_amc_duration(frm) {
    if (!frm.doc.start_date || !frm.doc.end_date) {
        set_amc_values(frm, 0, 0);
        return;
    }

    const start = frappe.datetime.str_to_obj(frm.doc.start_date);
    const end = frappe.datetime.str_to_obj(frm.doc.end_date);

    if (start > end) {
        frappe.msgprint(__('End Date must be after Start Date'));
        set_amc_values(frm, 0, 0);
        return;
    }

    const total_months = get_amc_months(start, end);
    set_amc_values(frm, Math.floor(total_months / 12), total_months);
}

// Inclusive month count, e.g. 01-Jan-25 -> 31-Dec-26 = 24, 15-Jan-25 -> 14-Feb-25 = 1.
// Mirrors get_amc_months() in crm_quotation.py - keep both in sync.
function get_amc_months(start, end) {
    // the end date is inclusive, so measure up to the day after it
    const till = new Date(end.getFullYear(), end.getMonth(), end.getDate() + 1);

    let months = (till.getFullYear() - start.getFullYear()) * 12 + (till.getMonth() - start.getMonth());

    // anchor = start date shifted by that many whole months
    const anchor = new Date(start.getFullYear(), start.getMonth() + months, start.getDate());
    if (anchor > till) {
        months -= 1;
    }

    // any leftover days count as a further (part) month
    const anchored = new Date(start.getFullYear(), start.getMonth() + months, start.getDate());
    if (anchored < till) {
        months += 1;
    }

    return Math.max(months, 0);
}

function set_amc_values(frm, years, months) {
    frm.set_df_property("amc_year", "read_only", 0);
    frm.set_df_property("amc_term", "read_only", 0);

    frm.set_value("amc_year", years);
    frm.set_value("amc_term", months);

    frm.set_df_property("amc_year", "read_only", 1);
    frm.set_df_property("amc_term", "read_only", 1);

    detect_multi_year(frm);
}

// Auto detect a multi year quotation purely from amc_year / amc_term.
function detect_multi_year(frm) {
    const is_multi_year = (cint(frm.doc.amc_term) > 12 || cint(frm.doc.amc_year) > 1) ? 1 : 0;

    if (cint(frm.doc.is_multi_year) !== is_multi_year) {
        frm.set_value("is_multi_year", is_multi_year);
    }

    set_default_print_format(frm);
}

// Multi year quotations default to the year-wise print format.
function set_default_print_format(frm) {
    const print_format = cint(frm.doc.is_multi_year)
        ? "AMC Offer Quote Multi Year"
        : "AMC Offer quote";

    // frm.meta IS locals.DocType["CRM Quotation"] (form.js: this.meta =
    // frappe.get_doc("DocType", this.doctype)) - the very object the DocType editor
    // binds to and saves. A plain assignment leaks into that save and trips
    // "Standard DocType cannot have default print format, use Customize Form".
    //
    // Defining it non-enumerable keeps it readable by frappe.meta.get_print_formats()
    // and the print view, while JSON.stringify - which is how the doc is sent to the
    // server - skips it entirely.
    try {
        Object.defineProperty(frm.meta, "default_print_format", {
            value: print_format,
            enumerable: false,
            writable: true,
            configurable: true,
        });
    } catch (e) {
        // a print-format preference must never stop the form from rendering
    }
}


frappe.ui.form.on("Contract Billing Schedule", {
    billed_date: function (frm, cdt, cdn) {
        console.log('workign')
        calculate_payment_due_date(frm, cdt, cdn);
    }
});

function calculate_payment_due_date(frm, cdt, cdn) {
    console.log('insi de workign')
    var row = locals[cdt][cdn]
    if (!frm.doc.payment_term) {
        return;
    }

    frappe.db.get_doc("Pay Term", frm.doc.payment_term).then(term_doc => {
        if (term_doc && term_doc.payment_term_portions && term_doc.payment_term_portions.length > 0) {
            // 🔹 Get row with minimum days
            let min_row = term_doc.payment_term_portions.reduce((prev, curr) => {
                return (curr.days || 0) < (prev.days || 0) ? curr : prev;
            });

            let min_days = min_row.days || 0;

            // 🔹 Add min_days to billed_date
            let billed_date_obj = frappe.datetime.str_to_obj(row.billed_date);
            billed_date_obj.setDate(billed_date_obj.getDate() + min_days);
            let payment_date = frappe.datetime.obj_to_str(billed_date_obj);
            console.log("payment date", payment_date)
            console.log("👉 billed_date:", row.billed_date);
            console.log("👉 min_days:", min_days);
            console.log("👉 calculated payment_date:", payment_date);
            // 🔹 Update field
            frappe.model.set_value(cdt, cdn, "payment_date", payment_date);
        }
    });
}
