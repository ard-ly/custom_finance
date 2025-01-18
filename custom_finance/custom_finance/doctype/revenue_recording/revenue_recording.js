// Copyright (c) 2024, custom_finance and contributors
// For license information, please see license.txt

frappe.ui.form.on("Revenue recording", {
	purpose: function(frm) {
        if(frm.doc.purpose){
			frappe.model.with_doc("Purpose", frm.doc.purpose, function() {
			    var tabletransfer= frappe.model.get_doc("Purpose", frm.doc.purpose)
			    frm.clear_table("accounts");

		        // Add first row
                var row1 = frm.add_child("accounts");
                row1.account = tabletransfer.purpose_debit_account;

                // Add second row
                var row2 = frm.add_child("accounts");
                row2.account = tabletransfer.purpose_credit_account;
                
		        frm.refresh_field("accounts");

			})
        }
    }
});
