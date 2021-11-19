# Copyright (c) 2021, Objekt klein a and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
import json 
import requests

class Ready2Order(Document):
	pass

@frappe.whitelist()
def import_products(from_date, to_date):
	print('LETS TO THIS')

	r2o_doc = frappe.get_single('Ready2Order')
	api_token = r2o_doc.user_token

	create_customer()

	invoice_docs = []
	invoices = get_invoices(api_token, from_date, to_date)

	for invoice in invoices:

		deliveryDate = invoice['invoice_deliveryDate']
		paidDate = invoice['invoice_paidDate']
		invoice_id = invoice['invoice_numberFull']
		items = invoice['items']
		discounts = invoice['discounts']
		invoice_items = create_sales_invoice_items(items)

		if invoice_items:
			invoice_doc = frappe.get_doc({
				'doctype': 'Sales Invoice',
				'name': invoice_id,
				'naming_series': 'RG.YYYY./.#####',
				'customer': 'Ready2Order',
				'posting_date': deliveryDate,
				'posting_time': deliveryDate,
				'set_posting_time': True,
				'due_date': paidDate,
				'items': invoice_items
			})

			if discounts:
				discount_value = discounts[0]['billDiscount_percent'] * -1
				invoice_doc.additional_discount_percent = discount_value

			invoice_docs.append(invoice_doc)

	print('Inserting ' + len(invoice_docs) + ' invoices.')

	for doc in invoice_docs:
			try: 
				doc.insert()
			except Exception as e:
				print(str(e))

	frappe.msgprint(msg='Invoices imported.', title='Done')

def create_customer():
	if not frappe.db.exists('Customer', 'Ready2Order'):
		customer_doc = frappe.get_doc({
			'doctype': 'Customer',
			'customer_name': 'Ready2Order'
		})
		customer_doc.insert()

def create_missing_product_group(group_name):
	if not frappe.db.exists('Item Group', group_name):
		group_doc = frappe.get_doc({
			'doctype': 'Item Group',
			'item_group_name': group_name,
			'parent_item_group': 'All Item Groups'
		})
		group_doc.insert()

def create_missing_product(item):

	group_name = item["productgroup_name"]
	create_missing_product_group(group_name)

	# create products
	id = item['product_id']
	name = item['item_name']
	price = item['item_price']

	if not frappe.db.exists('Item', id):
		item_doc = frappe.get_doc({
			'doctype': 'Item',
			'item_code': str(id),
			'item_name': name,
			'item_group': group_name
		})
		item_doc.insert()

		item_price_doc = frappe.get_doc({
			'doctype': 'Item Price',
			'item_code': str(id),
			'price_list': 'Standard Selling',
			'price_list_rate': price
		})
		item_price_doc.insert()
		print('Created price')

def create_sales_invoice_items(items):

	invoice_items = []

	for item in items:

		id = item['product_id']
		qty = item['item_qty']
		price = item['item_price']

		create_missing_product(item)
		invoice_items.append(frappe.get_doc({
			'doctype': 'Sales Invoice Item',
			'item_code': id,
			'qty': qty,
			'rate': price,
			'income_account': '8400 - Erlöse USt. 19% - OKA'
		}))

	return invoice_items

def create_sales_return_items(items):

	invoice_items = []

	for item in items:

		id = item['product_id']
		qty = item['item_qty']
		price = item['item_price']

		if price < 0:
			create_missing_product(item)
			invoice_items.append(frappe.get_doc({
				'doctype': 'Sales Invoice Item',
				'item_code': id,
				'qty': -qty,
				'rate': -price
			}))

	return invoice_items

def get_invoices(token, from_date, to_date):
	print('IM HERE')
	frappe.publish_progress('msgprint', 'Requesting invoices...')
	invoices_all = []

	limit = 100
	offset = 0
	invoices = request(token, from_date, to_date, limit, offset)
	
	while invoices:
		invoices_all = invoices_all + invoices
		offset += limit
		invoices = request(token, from_date, to_date, limit, offset)

	frappe.publish_realtime('msgprint', 'Got ' + str(len(invoices_all)) + ' invoices.')
	return invoices_all

def request(token, from_date, to_date, limit, offset):
	headers = {"Authorization": "Bearer " + token}
	base = 'https://api.ready2order.com/v1/document/invoice'
	url = base + '?' + 'limit=' + str(limit) + '&offset=' + str(offset) + '&items=true&discounts=true&dateFrom=' + from_date + '&dateTo=' + to_date
	response = requests.get(url, headers=headers).json()['invoices']
	return response 