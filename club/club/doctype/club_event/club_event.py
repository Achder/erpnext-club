# -*- coding: utf-8 -*-
# Copyright (c) 2021, Objekt klein a and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document

class ClubEvent(Document):
	pass

@frappe.whitelist()
def create_purchase_orders(doc):
	event = json.loads(doc)
	shifts = frappe.db.get_list('Shift', filters={
		'event': event['name']
	})
	for shift in shifts:
		shift_doc = frappe.get_doc('Shift', shift['name'])
		print(shift_doc.start)
	
@frappe.whitelist()
def get_events(start, end):
	if not frappe.has_permission("Club Event", "read"):
		raise frappe.PermissionError

	return frappe.db.sql("""select
		start,
		end,
		name,
		event_name
	from `tabClub Event`
	where `start` between %(start)s and %(end)s
	or `end` between %(start)s and %(end)s""", {
		"start": start,
		"end": end
	}, as_dict=True)