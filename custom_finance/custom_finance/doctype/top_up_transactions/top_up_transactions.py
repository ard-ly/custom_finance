# Copyright (c) 2024, custom_finance and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TopupTransactions(Document):
    def before_insert(self):
        self.reference_number = None
        self.reference_date = None

    def on_submit(self):
        # Ensure the transactions_account table is not empty
        if not self.transactions_account:
            frappe.throw("The transactions_account table is empty. Cannot create a Journal Entry.")

        # Create a new Journal Entry
        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "posting_date": self.posting_date,
            "custom_operation_type": self.operation_type,  # Custom field in JE
            "accounts": []
        })

        # Populate the accounts table
        for row in self.transactions_account:
            if row.debit and row.credit:
                frappe.throw(f"Both debit and credit are set for account {row.account}. Please fix the data.")
            elif not (row.debit or row.credit):
                frappe.throw(f"No debit or credit set for account {row.account}. Please fix the data.")

            journal_entry.append("accounts", {
                "account": row.account,
                "debit_in_account_currency": row.debit or 0,
                "credit_in_account_currency": row.credit or 0,
                "party_type": row.party_type if row.party_type else None,
                "party": row.party if row.party else None,
                # Add other optional fields like cost_center if needed
            })

        # Save and submit the Journal Entry
        if journal_entry.accounts:
            journal_entry.insert()
            journal_entry.submit()

            # Set the journal entry details into the current doc
            self.reference_number = journal_entry.name
            self.reference_date = journal_entry.posting_date
            self.db_update()  # Save changes to DB

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


