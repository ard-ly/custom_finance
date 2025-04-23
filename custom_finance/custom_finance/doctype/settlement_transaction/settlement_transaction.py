# Copyright (c) 2024, custom_finance and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SettlementTransaction(Document):
    def before_insert(self):
        self.reference_number = None
        self.reference_date = None
        
    def on_submit(self):
        # Validate that the accounts table is not empty
        if not self.accounts:
            frappe.throw("The accounts table is empty. Cannot create a Journal Entry.")

        # Create a new Journal Entry
        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "posting_date": self.date,  # Replace with your actual posting date field
            "accounts": []
        })

        # Populate the accounts table in the Journal Entry
        for row in self.accounts:
            # Skip if neither debit nor credit is provided
            if not (row.debit or row.credit):
                frappe.msgprint(f"Skipping row with account {row.account} as neither debit nor credit is set.")
                continue

            journal_entry.append("accounts", {
                "account": row.account,
                "debit_in_account_currency": row.debit or 0,
                "credit_in_account_currency": row.credit or 0,
                "party_type": row.party_type,
                "party": row.party,
                "cost_center": self.cost_center or None,
                "territory": self.territory or None,
                "driver_type": self.driver_type or None,
                "wallet_type": self.wallet_type or None,
            })

        # Save and submit the Journal Entry
        if journal_entry.accounts:
            journal_entry.insert()
            journal_entry.submit()

            # Set the Journal Entry reference in the current doc
            self.reference_number = journal_entry.name
            self.reference_date = journal_entry.posting_date
            self.db_update()  # Save changes

            frappe.msgprint(
                f"Journal Entry <a href='/app/journal-entry/{journal_entry.name}' target='_blank'>{journal_entry.name}</a> created successfully for Cash Transfers to Merchants {self.name}."
            )
        else:
            frappe.throw("No valid account entries were found to create a Journal Entry.")

    def on_cancel(self):
        if self.reference_number:
            try:
                je = frappe.get_doc("Journal Entry", self.reference_number)
                if je.docstatus == 1:
                    je.cancel()
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Failed to cancel linked Journal Entry")

    def on_trash(self):
        if self.reference_number:
            try:
                frappe.delete_doc("Journal Entry", self.reference_number, ignore_permissions=True)
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Failed to delete linked Journal Entry")


