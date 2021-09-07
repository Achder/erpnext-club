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
def import_products():
	r2o_doc = frappe.get_single('Ready2Order')
	api_token = r2o_doc.user_token
	headers = {"Authorization": "Bearer " + api_token}
	products = requests.get('https://api.ready2order.com/v1/products?includeProductVariations=true&includeProductGroup=true', headers=headers).json()

	for product in products:
		print("--------------------------")
		print(product["product_name"])
		print(product["product_price"])
		print(product["product_vat"])
		print(product["product_active"])

		# product_type_id: product_type
		#		none: regular product
		# 	5: 		variation
		#		19: 	deposit sale
		print(product["product_type"])
		print(product["product_type_id"])
		
		print(product["productgroup"]["productgroup_name"])
		
		if "productvariation" in product:
			print(product["productvariation"])

		# TODO
		#		check if product group exists
		#		create product group if not exists
		#
		# 	check if product exists
		#	 	create product if not exists
		#
		#		create price
