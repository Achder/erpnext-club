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
	
	pos = frappe.db.get_list('Purchase Order', filters={'event': event["name"]})
	if pos:
		frappe.throw(
			title='Error',
			msg="""There already exist purchase orders for this event. 
			You will most likely create duplicates. 
			Either check if new orders need to be created or delete all of the old ones."""
		)
		return

	create_shift_purchase_orders(event)
	create_booking_purchase_orders(event)
	create_renting_purchase_orders(event)
	create_promo_purchase_orders(event)
	create_kitchen_purchase_orders(event)
	create_uncategorized_purchase_orders(event)

	frappe.msgprint(
    msg='Please check all entries for correctness and submit afterwards!',
    title='Created'
	)

@frappe.whitelist()
def create_sales_orders(doc):
	event = json.loads(doc)
	create_entrance_sales_orders(event)
	frappe.msgprint(
    msg='Please check all entries for correctness and submit afterwards!',
    title='Created'
	)

@frappe.whitelist()
def import_pos(doc):
	event = json.loads(doc)
	start = event["start"]
	end = event["end"]
	frappe.enqueue('club.club.doctype.ready2order.ready2order.import_products', from_date=start, to_date=end)
	return doc

def create_entrance_sales_orders(event):

	entrances = event['entrances']
	sales_order_items = []

	for entrance in entrances:
		sales_order_items.append(frappe.get_doc({
			'doctype': 'Sales Order Item',
			'item_code': 'entrance',
			'qty': entrance["nb_of_guests"],
			'rate': entrance["price"],
			'delivery_date': entrance["start"]
		}))

	sales_order = frappe.get_doc({
		'doctype': 'Sales Order',
		'customer': 'Entrance',
		'items': sales_order_items,
		'date': event["start"],
		'delivery_date': frappe.utils.today(),
		'event': event["name"]
	})

	sales_order.insert()

	frappe.msgprint(
    msg='Entrance orders created.',
    title='Created'
	)

def create_shift_purchase_orders(event):

	shifts = frappe.db.get_list('Shift', filters={'event': event["name"]})
	po_docs = []

	for shift in shifts:
		shift_doc = frappe.get_doc('Shift', shift['name'])

		if shift_doc.worker_type != 'Supplier' or not shift_doc.sends_invoice:
			continue

		hours = frappe.utils.time_diff(shift_doc.end, shift_doc.start).total_seconds() / 3600

		po_docs.append(
			create_po(
				supplier=shift_doc.worker,
				items=[create_poi(shift_doc.job, hours, 11)],
				event=event['name']
			)
		)

	for po_doc in po_docs:
		po_doc.insert()

	frappe.msgprint(
    msg='Shift orders created.',
    title='Created'
	)

def create_booking_purchase_orders(event):

	bookings = frappe.db.get_list('Booking', filters={'event': event["name"]})
	po_docs = []

	for booking in bookings:
		booking_doc = frappe.get_doc('Booking', booking['name'])

		po_docs.append(
			create_po(
				supplier=booking_doc.artist,
				items=[
					create_poi(
						item_code='artist_fee', 
						qty=1, 
						rate=booking_doc.artist_fee
					)
				],
				event=event['name']
			)
		)

		if booking_doc.include_booker:
			po_docs.append(
				create_po(
					supplier=booking_doc.booker,
					items=[
						create_poi(
							item_code='booking_fee', 
							qty=1, 
							rate=booking_doc.booking_fee
						)
					],
					event=event['name']
				)
			)

		if booking_doc.include_hotel:
			po_docs.append(
				create_po(
					supplier=booking_doc.hotel,
					items=[
						create_poi(
							item_code='hotel_fee', 
							qty=1, 
							rate=booking_doc.hotel_fee
						)
					],
					event=event['name']
				)
			)

	for po_doc in po_docs:
		po_doc.insert()

	frappe.msgprint(
    msg='Booking orders created.',
    title='Created'
	)

def create_renting_purchase_orders(event):

	rentings = frappe.db.get_list('Renting Costs', filters={'event': event["name"]})

	for renting in rentings:
		renting_doc = frappe.get_doc('Renting Costs', renting['name'])
		po_doc = create_po(
			supplier=renting_doc.supplier,
			items=[
				create_poi(
					item_code=renting_doc.item, 
					qty=1, 
					rate=renting_doc.cost
				)
			],
			event=event['name']
		)

		po_doc.insert()

	frappe.msgprint(
    msg='Renting costs orders created.',
    title='Created'
	)

def create_promo_purchase_orders(event):

	promos = frappe.db.get_list('Promo Costs', filters={'event': event["name"]})

	for promo in promos:
		promo_doc = frappe.get_doc('Promo Costs', promo['name'])
		po_doc = create_po(
			supplier=promo_doc.supplier,
			items=[
				create_poi(
					item_code=promo_doc.item, 
					qty=1, 
					rate=promo_doc.cost
				)
			],
			event=event['name']
		)

		po_doc.insert()

	frappe.msgprint(
    msg='Promo costs orders created.',
    title='Created'
	)

def create_kitchen_purchase_orders(event):

	kitchens = frappe.db.get_list('Kitchen Costs', filters={'event': event["name"]})

	for kitchen in kitchens:
		kitchen_doc = frappe.get_doc('Kitchen Costs', kitchen['name'])
		po_doc = create_po(
			supplier=kitchen_doc.supplier,
			items=[
				create_poi(
					item_code=kitchen_doc.item, 
					qty=1, 
					rate=kitchen_doc.cost
				)
			],
			event=event['name']
		)

		po_doc.insert()

	frappe.msgprint(
    msg='Kitchen costs orders created.',
    title='Created'
	)
	
def create_uncategorized_purchase_orders(event):

	uncategorizeds = frappe.db.get_list('Uncategorized Costs', filters={'event': event["name"]})

	for uncategorized in uncategorizeds:
		uncategorized_doc = frappe.get_doc('Uncategorized Costs', uncategorized['name'])
		po_doc = create_po(
			supplier=uncategorized_doc.supplier,
			items=[
				create_poi(
					item_code=uncategorized_doc.item, 
					qty=1, 
					rate=uncategorized_doc.cost
				)
			],
			event=event['name']
		)

		po_doc.insert()

	frappe.msgprint(
    msg='Uncategorized costs orders created.',
    title='Created'
	)

def create_po(supplier, items, event):
	return frappe.get_doc({
		'doctype': 'Purchase Order',
		'supplier': supplier,
		'items': items,
		'schedule_date': frappe.utils.today(),
		'event': event
	})

def create_poi(item_code, qty, rate):
	return frappe.get_doc({
		'doctype': 'Purchase Order Item',
		'item_code': item_code,
		'qty': qty,
		'rate': rate
	})

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