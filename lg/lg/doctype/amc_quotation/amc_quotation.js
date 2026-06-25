// Copyright (c) 2025, extension and contributors
// For license information, please see license.txt

// frappe.ui.form.on("AMC Quotation", {
// 	refresh(frm) {

// 	},
// });
// frappe.ui.form.on("AMC Quotation", {
//     project_type: function(frm) {
//         fetch_zone_from_vertical(frm)
//     },
//     quoted_price: function(frm) {
//         fetch_zone_from_vertical(frm)
//     },
//     horse_power: function(frm) {
//         fetch_zone_from_vertical(frm)
//     },

    
// });

// function fetch_zone_from_vertical(frm) {
//         if (frm.doc.project_type && frm.doc.quoted_price && frm.doc.horse_power) {
//             frappe.call({
//                 method:  "lg.lg.doctype.vertical_master.vertical_master.get_zone_from_vertical_master",  // మీ python ఫంక్షన్ full path ఇక్కడ పెట్టాలి
//                 args: {
//                     project_type: frm.doc.project_type,
//                     quoted_price: frm.doc.quoted_price,
//                     horse_power: frm.doc.horse_power
//                 },
//                 callback: function(r) {
//                     console.log("res",r)
//                     if (r.message && r.message.zone) {
//                         frm.set_value("zone", r.message.zone);
//                     } else {
//                         frappe.msgprint(r.message.error || "Matching Zone not found for given HP and Quoted Price.");
//                         frm.set_value("zone", "");
//                     }
//                 }
//             });
//         }
//     }
// //     Server error occurred.

// frappe.ui.form.on('AMC Quotation', {
//     // Trigger when these fields are changed
//     horse_power: function(frm) {
//         fetch_zone(frm);
//     },
//     quoted_price: function(frm) {
//         fetch_zone(frm);
//     },
//     project_type: function(frm) {
//         fetch_zone(frm);
//     }
// });

// // Utility function to fetch zone
// function fetch_zone(frm) {
//     if (!(frm.doc.horse_power && frm.doc.quoted_price && frm.doc.project_type)) {
//         return;  // Wait until all values are filled
//     }

//     frappe.call({
//         method: "lg.lg.doctype.vertical_master.vertical_master.get_zone_from_vertical_master", // Change to your actual method
//         args: {
//             horse_power: frm.doc.horse_power,
//             quoted_price: frm.doc.quoted_price,
//             project_type: frm.doc.project_type
//         },
//         callback: function(r) {
//             console.log("Raw server response:", r); // For debugging

//             if (r && r.message) {
//                 if (r.message.zone) {
//                     frm.set_value("zone", r.message.zone);
//                 } else if (r.message.error) {
//                     frappe.msgprint(r.message.error);
//                     frm.set_value("zone", "");
//                 } else {
//                     frappe.msgprint("Zone not found.");
//                     frm.set_value("zone", "");
//                 }
//             } else {
//                 frappe.msgprint("No response from server.");
//                 frm.set_value("zone", "");
//             }
//         }
//     });
// }
// frappe.ui.form.on('AMC Quotation', {
//     horse_power: function(frm) {
//         fetch_zone(frm);
//     },
//     quoted_price: function(frm) {
//         fetch_zone(frm);
//     },
//     project_type: function(frm) {
//         fetch_zone(frm);
//     }
// });

// function fetch_zone(frm) {
//     if (!(frm.doc.horse_power && frm.doc.quoted_price && frm.doc.project_type)) {
//         return; // Wait until all required fields are filled
//     }

//     frappe.call({
//         method: "lg.lg.doctype.vertical_master.vertical_master.get_zone_from_vertical_master",
//         args: {
//             horse_power: frm.doc.horse_power,
//             quoted_price: frm.doc.quoted_price,
//             project_type: frm.doc.project_type
//         },
//         callback: function(r) {
//             console.log("Raw server response:", r);

//             if (r && r.message) {
//                 if (r.message.zone) {
//                     frm.set_value("zone", r.message.zone);
//                 } else if (r.message.error) {
//                     frappe.msgprint(r.message.error);
//                     frm.set_value("zone", "");
//                 } else {
//                     frappe.msgprint("Zone not found.");
//                     frm.set_value("zone", "");
//                 }
//             } else {
//                 frappe.msgprint("No response from server.");
//                 frm.set_value("zone", "");
//             }
//         }
//     });
// }
frappe.ui.form.on('AMC Quotation', {
    quoted_price: function(frm) {
        fetch_zone(frm);
    },
    horse_power: function(frm) {
        fetch_zone(frm);
    },
    project_type: function(frm) {
        fetch_zone(frm);
    }
});

function fetch_zone(frm) {
    if (frm.doc.horse_power && frm.doc.quoted_price && frm.doc.project_type) {
        frappe.call({
            method: "lg.lg.doctype.vertical_master.vertical_master.get_zone_from_vertical_master", // change path if needed
            args: {
                horse_power: frm.doc.horse_power,
                quoted_price: frm.doc.quoted_price,
                project_type: frm.doc.project_type
            },
            callback: function(r) {
                if (r.message) {
                    if (r.message.zone) {
                        frm.set_value("zone", r.message.zone);
                    } else {
                        frm.set_value("zone", "");
                        frappe.msgprint(r.message.error || "Zone not found");
                    }
                }
            }
        });
    }
}
