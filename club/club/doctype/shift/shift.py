# -*- coding: utf-8 -*-
# Copyright (c) 2021, Objekt klein a and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Shift(Document):
	pass

@frappe.whitelist()
def get_shifts(start, end):
	if not frappe.has_permission("Shift", "read"):
		raise frappe.PermissionError

	return frappe.db.sql("""select
		start,
		end,
		name,
		job,
		employee
	from `tabShift`
	where `start` between %(start)s and %(end)s""", {
		"start": start,
		"end": end
	}, as_dict=True)