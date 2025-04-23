// Copyright (c) 2024, custom_finance and contributors
// For license information, please see license.txt

frappe.ui.form.on("Top-up Transactions", {
    refresh: function(frm) {
        frm.fields_dict["transactions_account"].grid.get_field("party_type").get_query = function(doc, cdt, cdn) {
            return {
                doctype: "Party Type",
            };
        };
    },
	operation_type: function(frm) {
        if(frm.doc.operation_type){
			frappe.model.with_doc("Operation Type", frm.doc.operation_type, function() {
			    var tabletransfer= frappe.model.get_doc("Operation Type", frm.doc.operation_type)
			    frm.clear_table("transactions_account");

		        // Add first row
                var row1 = frm.add_child("transactions_account");
                row1.account = tabletransfer.operation_debit_account;

                // Add second row
                var row2 = frm.add_child("transactions_account");
                row2.account = tabletransfer.operation_credit_account;
                
		        frm.refresh_field("transactions_account");

			})
        }
    }
});

frappe.ui.form.on("Accounts", {
    party_type:function(frm, cdt, cdn){
        var child = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "party", null);
    }
});
