# Copyright (c) 2025, Omar Jaber and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from pymysql import MySQLError
from frappe.utils import cint, cstr, flt, nowdate, comma_and, date_diff, getdate, time_diff, time_diff_in_hours, now_datetime
from datetime import datetime

class TransactionImport(Document):
    @frappe.whitelist()
    def import_transaction_data(self):
        directory_type = 'public'
        if '/private/' in self.attach_file:
            directory_type = 'private'

        from frappe.utils.csvutils import read_csv_content
        file_name = self.attach_file.split('/')[-1]
        file_path = frappe.get_site_path(directory_type, 'files', file_name)

        try:
            with open(file_path, "r") as infile:
                rows = read_csv_content(infile.read())
                success_count = 0
                i = 0
                for index, row in enumerate(rows):
                    # skip header
                    if index == 0:
                        continue

                    # Skip completely empty rows
                    if not any(row):
                        continue

                    transaction_number = row[0]
                    operation_type_name = row[1]
                    datetime_str = row[2]
                    territory_name = row[3]
                    driver_type = row[4]
                    wallet_type = row[5]
                    party_type_from = row[6]
                    party_from = row[7]
                    party_type_to = row[8]
                    party_to = row[9]
                    amount = row[10]

                    if self.transaction_type=='Top-up Transactions':
                        if transaction_number and operation_type_name:
                            if not frappe.db.exists("Top-up Transactions", {"transaction_number": transaction_number}):
                                # Check Operation Type
                                operation_doc = frappe.db.get_value("Operation Type", {"operation_type_name": operation_type_name}, ["name", "operation_debit_account", "operation_credit_account"], as_dict=True)
                                if not operation_doc:
                                    frappe.throw(f"Operation Type '{operation_type_name}' in row {index+1} does not exist!", alert=True, indicator='red')
                                    continue

                                try:
                                    doc = frappe.new_doc("Top-up Transactions")
                                    doc.transaction_number = transaction_number
                                    doc.transaction_datetime = parse_datetime(datetime_str)
                                    doc.driver_type = driver_type
                                    doc.wallet_type = wallet_type
                                    territory = create_territory_if_not_exists(territory_name)
                                    doc.territory = territory

                                    doc.flags.ignore_validate = True
                                    doc.flags.ignore_mandatory = True
                                    doc.save(ignore_permissions=True)
                                    frappe.db.commit()
                                except MySQLError as e:
                                    if e.args[0] == 1292:
                                        frappe.msgprint("Error!", alert=True, indicator='red')
                                        return f"Incorrect date value: {e.args[1]}"
                                    else:
                                        frappe.msgprint("Error!", alert=True, indicator='red')
                                        return f"Error: {e.args[1]}"
                                    continue

                                i+=1
                                print(f"- Successfully add mail: {row[4]}")
                                frappe.msgprint(f"- Successfully add mail: {row[4]}", alert=True, indicator='green')
                    
                    elif self.transaction_type=='Outgoing Mail':
                        if row[0] and row[2] and row[3] and row[4]:
                            if not frappe.db.exists("Outgoing Mail", {"reference_number": row[1]}):
                                try:
                                    doc = frappe.new_doc("Outgoing Mail")
                                    doc.update({
                                        "doctype":"Outgoing Mail",
                                        "message_registration_date": convert_date_format(str(row[0])),
                                        "reference_number": row[1],
                                        "from": row[2],
                                        "to": row[3],
                                        "message_subject": row[4],
                                        "notes": row[5],
                                        "docstatus": 1
                                    })
                                    doc.flags.ignore_validate = True
                                    doc.flags.ignore_mandatory = True         
                                    doc.save(ignore_permissions=True)
                                    frappe.db.commit()
                                except MySQLError as e:
                                    if e.args[0] == 1292:
                                        frappe.msgprint("Error!", alert=True, indicator='red')
                                        return f"Incorrect date value: {e.args[1]}"
                                    else:
                                        frappe.msgprint("Error!", alert=True, indicator='red')
                                        return f"Error: {e.args[1]}"
                                    continue

                                i+=1
                                print(f"- Successfully add mail: {row[4]}")
                                frappe.msgprint(f"- Successfully add mail: {row[4]}", alert=True, indicator='green')
                    
                    else:
                        return "Missing Data!" 
                print('*************')
                frappe.msgprint("Success!", alert=True, indicator='green')
                return f"Total mail added: {i}"
        except Exception as e:
            frappe.msgprint("Error!", alert=True, indicator='red')
            return f"An error occurred: {e}"
            


def create_territory_if_not_exists(territory_name):
    territory = frappe.db.exists("Territory", {"territory_name": territory_name})
    if not territory:
        doc = frappe.new_doc("Territory")
        doc.territory_name = territory_name
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    return territory


def create_driver_type_if_not_exists(driver_type_name):
    driver_type = frappe.db.exists("Driver Type", {"type": driver_type_name})
    if not driver_type:
        doc = frappe.new_doc("Driver Type")
        doc.type = driver_type_name
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    return driver_type

def create_wallet_type_if_not_exists(wallet_type_name):
    wallet_type = frappe.db.exists("Wallet Type", {"type": wallet_type_name})
    if not wallet_type:
        doc = frappe.new_doc("Wallet Type")
        doc.type = wallet_type_name
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    return wallet_type


def parse_datetime(value):
    if not value:
        return now_datetime()
    try:
        return datetime.datetime.strptime(value, "%d/%m/%Y %H:%M")
    except ValueError:
        frappe.throw(f"Invalid datetime format: {value}. Expected format: DD/MM/YYYY HH:MM")



def convert_date_format(date_str):
    # List of possible date formats that the user might use
    date_formats = [
        "%d-%m-%Y",  # DD-MM-YYYY (e.g., 10-02-2005)
        "%d/%m/%Y",  # DD/MM/YYYY (e.g., 10/02/2005)
        "%Y-%m-%d",  # YYYY-MM-DD (e.g., 2005-02-10)
        "%Y/%m/%d",  # YYYY/MM/DD (e.g., 2005/02/10)
        "%d.%m.%Y",  # DD.MM.YYYY (e.g., 10.02.2005)
        "%m-%d-%Y",  # MM-DD-YYYY (e.g., 02-10-2005)
        "%m/%d/%Y"   # MM/DD/YYYY (e.g., 02/10/2005)
    ]
    
    for date_format in date_formats:
        try:
            # Attempt to parse the date string with each format
            date_obj = datetime.strptime(date_str, date_format)
            # Return the date in ERPNext format YYYY-MM-DD
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            # Continue to the next format if parsing fails
            continue

    # If no format matched, log the error and return None
    frappe.msgprint(f"Error in date format conversion: Invalid date format '{date_str}'", alert=True, indicator='red')
    return None


