// Copyright (c) 2025, Omar Jaber and contributors
// For license information, please see license.txt

frappe.ui.form.on("Transaction Import", {
	transaction_type: function(frm) {
		frm.set_value("output", )		
	},
	download_template: function(frm) {
		if(frm.doc.transaction_type=='Top-up Transactions'){
			window.location.href = '/assets/custom_finance/file/top_up_transactions_template.csv';
		}else{
			window.location.href = '/assets/custom_finance/file/settlement_transaction_template.csv';
		}
	},
	attach_file: function (frm) {
    	frm.set_value("output", )
    },
    get_data: function (frm) {
    	if(frm.doc.attach_file && frm.doc.transaction_type){

            frappe.call({
		        doc: cur_frm.doc,
		        method: "import_transaction_data",
		        callback: function(r) {
		        	frm.set_value('output', r.message)
		            cur_frm.refresh_fields(['output']);
		        }
		    });
	    }else{
	    	frappe.throw("Please attach a file first.")
	    }
    }
});
