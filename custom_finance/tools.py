# -*- coding:utf-8 -*-
# encoding: utf-8

# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from __future__ import division
import frappe
import frappe, os , math
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_site_base_path, cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, \
    comma_or, get_fullname, add_years, add_months, add_days, nowdate
from frappe.utils.data import flt, nowdate, getdate, cint, rounded, add_months, add_days, get_last_day
from frappe.utils.password import update_password as _update_password
from frappe.utils import cint, cstr, flt, nowdate, comma_and, date_diff, getdate, formatdate ,get_url
import datetime
import traceback
from datetime import date
from frappe.model.mapper import get_mapped_doc
import sys
from frappe.utils import cstr
from frappe.model.document import Document
import json




def add_chart_of_account():
    print('*** Add Chart of Accounts ***')
    from frappe.utils.csvutils import read_csv_content
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'Chart of Accounts.csv')
    try:
        with open(file_path, "r", encoding="utf-8") as infile:
            rows = read_csv_content(infile.read())
            i = 0
            for index, row in enumerate(rows):

                if index!=0:
                    if row[0] and not frappe.db.exists("Account", {"account_name": row[0]}):
                        print(row[0])

                        parent_account = None
                        if row[1]:
                            parent_account = frappe.db.get_value("Account", {"account_number": row[3]}, "name")

                        try:
                            doc = frappe.new_doc("Account")
                            doc.update({
                                "doctype":"Account",
                                "account_name": row[0],
                                "parent_account": parent_account,
                                "account_number": row[2],
                                "is_group": row[4],
                                "account_type": row[5],
                                "root_type": row[6],
                                "account_currency": 'LYD'
                            })
                            if not row[1]:
                                doc.flags.ignore_mandatory = True
                            doc.save(ignore_permissions=True)
                            frappe.db.commit()
                        except Exception as e:
                            print(f"Error at row {index}: {e}")
                            return


                        i+=1
                        print(row[0])
                    
            print('*************')
            print(f"Total Accounts added: {i}")
    except Exception as e:
        print(f"An error occurred: {e}")



def add_party_type():
    party_types = ["Driver", "User"]
    
    for party_type in party_types:
        if not frappe.db.exists("Party Type", {"name": party_type}):
            try:
                party_type_doc = frappe.new_doc("Party Type")
                party_type_doc.update({
                    "doctype": "Party Type",
                    "name": party_type,
                    "party_type": party_type,
                    "account_type": "Payable",
                })
                party_type_doc.save(ignore_permissions=True)
                frappe.db.commit()
                print(f"Added '{party_type}' as Party Type")
            except Exception as e:
                print(f"Error while adding '{party_type}' Party Type: {e}")




