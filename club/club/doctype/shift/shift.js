// Copyright (c) 2021, Objekt klein a and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shift', {
	setup: (frm) => {
		frm.set_query("worker_type", () => ({
			filters: [
				["name", "in", ["Employee", "Supplier"]]
			]
		}))
		frm.set_query("job", () => ({
			filters: [
				["item_group", "like", "Job"]
			]
		}))
	},
});
