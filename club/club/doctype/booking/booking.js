// Copyright (c) 2021, Objekt klein a and contributors
// For license information, please see license.txt

frappe.ui.form.on('Booking', {
	setup: (frm) => {
		frm.set_query("artist", () => ({
			filters: [
				["supplier_group", "like", "Artist"]
			]
		}))
		frm.set_query("booker", () => ({
			filters: [
				["supplier_group", "like", "Booker"]
			]
		}))
		frm.set_query("hotel", () => ({
			filters: [
				["supplier_group", "like", "Hotel"]
			]
		}))
	},
});
