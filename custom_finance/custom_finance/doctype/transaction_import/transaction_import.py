# Copyright (c) 2025, Omar Jaber and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from pymysql import MySQLError
from frappe.utils import cint, cstr, flt, nowdate, comma_and, date_diff, getdate, get_datetime, time_diff, time_diff_in_hours, now_datetime
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

        success_count = 0
        error_messages = []
        added_transactions = []

        try:
            with open(file_path, "r") as infile:
                rows = read_csv_content(infile.read())

                for index, row in enumerate(rows):
                    # skip header or empty rows
                    if index == 0 or not any(row):
                        continue

                    transaction_number = row[0]
                    type_or_purpose_name = row[1]
                    datetime_str = row[2]
                    territory_name = row[3]
                    driver_type_name = row[4]
                    wallet_type_name = row[5]
                    party_type_from = row[6]
                    party_from = row[7]
                    party_type_to = row[8]
                    party_to = row[9]
                    amount = row[10]

                    if not (transaction_number and type_or_purpose_name):
                        error_messages.append(f"Row {index+1}: Missing transaction number or type/purpose.")
                        continue

                    if self.transaction_type=='Top-up Transactions':
                        if frappe.db.exists("Top-up Transactions", {"transaction_number": transaction_number}):
                            error_messages.append(f"Row {index+1}: Transaction number '{transaction_number}' already exists.")
                            continue

                        operation_doc = frappe.db.get_value(
                            "Operation Type",
                            {"operation_type_name": type_or_purpose_name},
                            ["name", "operation_debit_account", "operation_credit_account"],
                            as_dict=True
                        )
                        if not operation_doc:
                            error_messages.append(f"Row {index+1}: Operation Type '{type_or_purpose_name}' not found.")
                            continue

                        try:
                            doc = frappe.new_doc("Top-up Transactions")
                            doc.transaction_number = transaction_number
                            doc.operation_type = operation_doc.name
                            doc.transaction_datetime = get_datetime(datetime_str)
                            doc.territory = create_territory_if_not_exists(territory_name)
                            doc.driver_type = create_driver_type_if_not_exists(driver_type_name)
                            doc.wallet_type = create_wallet_type_if_not_exists(wallet_type_name)
                            
                            # Child Table Entries
                            debit_entry = {
                                "account": operation_doc.operation_debit_account,
                                "debit": amount or 0,
                                "credit": 0,
                                "party_type": party_type_from,
                                "party": party_from
                            }

                            credit_entry = {
                                "account": operation_doc.operation_credit_account,
                                "debit": 0,
                                "credit": amount or 0,
                                "party_type": party_type_to,
                                "party": party_to
                            }

                            doc.append("transactions_account", debit_entry)
                            doc.append("transactions_account", credit_entry)
                            
                            doc.save(ignore_permissions=True)
                            doc.submit()
                            frappe.db.commit()
                            success_count += 1
                            added_transactions.append(transaction_number)

                        except Exception as e:
                            error_messages.append(f"Row {index+1}: ❌ {str(e)}")
                            frappe.db.rollback()
                            continue

                    elif self.transaction_type=='Settlement Transaction':
                        if frappe.db.exists("Settlement Transaction", {"transaction_number": transaction_number}):
                            error_messages.append(f"Row {index+1}: Transaction number '{transaction_number}' already exists.")
                            continue

                        purpose_doc = frappe.db.get_value(
                            "Purpose",
                            {"purpose_name": type_or_purpose_name},
                            ["name", "purpose_debit_account", "purpose_credit_account"],
                            as_dict=True
                        )
                        if not purpose_doc:
                            error_messages.append(f"Row {index+1}: Purpose '{type_or_purpose_name}' not found.")
                            continue
                        
                        try:
                            doc = frappe.new_doc("Settlement Transaction")
                            doc.transaction_number = transaction_number
                            doc.purpose = purpose_doc.name
                            doc.transaction_datetime = get_datetime(datetime_str)
                            doc.territory = create_territory_if_not_exists(territory_name)
                            doc.driver_type = create_driver_type_if_not_exists(driver_type_name)
                            doc.wallet_type = create_wallet_type_if_not_exists(wallet_type_name)

                            # Child Table Entries
                            debit_entry = {
                                "account": purpose_doc.purpose_debit_account,
                                "debit": amount or 0,
                                "credit": 0,
                                "party_type": party_type_from,
                                "party": party_from
                            }

                            credit_entry = {
                                "account": purpose_doc.purpose_credit_account,
                                "debit": 0,
                                "credit": amount or 0,
                                "party_type": party_type_to,
                                "party": party_to
                            }

                            doc.append("accounts", debit_entry)
                            doc.append("accounts", credit_entry)
                            
                            doc.docstatus = 1

                            doc.save(ignore_permissions=True)
                            doc.submit()
                            frappe.db.commit()
                            success_count += 1
                            added_transactions.append(transaction_number)

                        except Exception as e:
                            error_messages.append(f"Row {index+1}: ❌ {str(e)}")
                            frappe.db.rollback()
                            continue
                
                    else:
                        error_messages.append(f"Invalid Transaction Type Selected.")
                

                # After processing all rows
                output_message = f"✅ {success_count} transactions imported successfully.\n"
                if added_transactions:
                    output_message += "\nAdded Transactions:\n" + "\n".join(added_transactions)

                if error_messages:
                    output_message += "\n\n⚠️ Issues Found:\n" + "\n".join(error_messages)

                self.output = output_message
                self.save(ignore_permissions=True)

                frappe.msgprint("Import finished. Check output field for details.", alert=True, indicator='green')
                return output_message

        except Exception as e:
            error_message = f"❌ Error occurred: {str(e)}"
            self.output = error_message
            self.save(ignore_permissions=True)
            frappe.msgprint(error_message, alert=True, indicator='red')
            return error_message
            


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
        converted = convert_datetime_format(value)
        if converted:
            return converted
        else:
            return now_datetime()
        return datetime.datetime.strptime(value, "%d/%m/%Y %H:%M")
    except ValueError:
        frappe.throw(f"Invalid datetime format: {value}. Expected format: DD/MM/YYYY HH:MM")


def convert_datetime_format(date_str):
    """Convert various possible formats to ERPNext datetime format (YYYY-MM-DD HH:MM:SS)."""
    # Possible datetime formats
    datetime_formats = [
        "%d-%m-%Y %H:%M",   # DD-MM-YYYY HH:MM
        "%d/%m/%Y %H:%M",   # DD/MM/YYYY HH:MM
        "%Y-%m-%d %H:%M",   # YYYY-MM-DD HH:MM
        "%Y/%m/%d %H:%M",   # YYYY/MM/DD HH:MM
        "%d.%m.%Y %H:%M",   # DD.MM.YYYY HH:MM
        "%m-%d-%Y %H:%M",   # MM-DD-YYYY HH:MM
        "%m/%d/%Y %H:%M",   # MM/DD/YYYY HH:MM
        "%d-%m-%Y",         # DD-MM-YYYY (date only, assume 00:00)
        "%d/%m/%Y",         # DD/MM/YYYY (date only)
        "%Y-%m-%d",         # YYYY-MM-DD (date only)
        "%Y/%m/%d",         # YYYY/MM/DD (date only)
        "%d.%m.%Y",         # DD.MM.YYYY (date only)
        "%m-%d-%Y",         # MM-DD-YYYY (date only)
        "%m/%d/%Y"          # MM/DD/YYYY (date only)
    ]

    for fmt in datetime_formats:
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            # If only date part provided, add time 00:00:00
            if "%H" not in fmt:
                dt = dt.replace(hour=0, minute=0, second=0)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    # If all formats fail
    frappe.msgprint(f"Error: Invalid datetime format '{date_str}'.", alert=True, indicator='red')
    return None



