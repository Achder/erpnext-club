// Copyright (c) 2021, Objekt klein a and contributors
// For license information, please see license.txt

const utils = {
	entrance: {
		interpolator: (start, end, entrances) => {
		
			// interpolation function and it's integral
			const fx = x => -x + 1
			const Fx = x => x - ((x * x) / 2)
		
			const duration = frappe.datetime.get_hour_diff(end, start)
			const normalized_dates = entrances.map(e => {
				return {
					price: e.price,
					start: frappe.datetime.get_hour_diff(e.start, start) / duration
				}
			})
		
			const total_area = Fx(1) - Fx(0)
			const areas = normalized_dates.map((nd, idx) => {
				const next = idx >= normalized_dates.length - 1 ? 1 : normalized_dates[idx+1].start
				return {
					price: nd.price,
					area: Fx(next) - Fx(nd.start)
				}
			})
			
			return {
				total_area,
				areas
			}
		},
		effective_price: (start, end, entrances) => {
			const {total_area, areas} = utils.entrance.interpolator(start, end, entrances)
			let price = 0
			for(const area of areas)
				price += area.area / total_area * area.price
			return price
		},
		project: (start, end, entrances, guests) => {
			const { total_area, areas} = utils.entrance.interpolator(start, end, entrances)
			let revenue_entrance = 0
			for(const area of areas)
				revenue_entrance += area.area / total_area * guests * area.price
			return revenue_entrance
		},
		count_guests: (entrances) => {
			let guests_total = 0
			for(const e of entrances)
				guests_total += e.nb_of_guests
			return guests_total
		},
		sum: (entrances) => {
			let revenue = 0
			for(const e of entrances) {
				const {nb_of_guests, price} = e
				revenue += price * nb_of_guests
			}
			return revenue
		},
	},

	booking: {
		sum: (bookings) => {
			let total = 0
			for(const booking of bookings) {
				const {artist_fee, include_booker, booking_fee, include_hotel, hotel_fee} = booking
				total += artist_fee
				total += include_booker ? booking_fee : 0
				total += include_hotel ? hotel_fee : 0
			}
			return total
		}
	},

	renting: {
		sum: (rentings) => {
			let total = 0
			for(const renting of rentings) {
				const {cost} = renting
				total += cost
			}
			return total
		}
	},

	promo: {
		sum: (promos) => {
			let total = 0
			for(const promo of promos) {
				const {cost} = promo
				total += cost
			}
			return total
		}
	},

	kitchen: {
		sum: (kitchens) => {
			let total = 0
			for(const kitchen of kitchens) {
				const {cost} = kitchen
				total += cost
			}
			return total
		}
	},

	uncategorized: {
		sum: (uncategorized_costs) => {
			let total = 0
			for(const uncategorized of uncategorized_costs) {
				const {cost} = uncategorized
				total += cost
			}
			return total
		}
	},

	shift: {
		fee: async (shift) => {
			const {job, start, end} = shift
			const price = await frappe.db.get_list('Item Price', {
				filters: {
					item_code: job
				},
				fields: ['price_list_rate']
			})
			const rate = price?.[0]?.price_list_rate ?? 0
			const duration = frappe.datetime.get_hour_diff(end, start)
			return rate * duration
		},
		sum: async (shifts) => {
			const costs = await Promise.all(shifts.map(async (shift) => {
				return utils.shift.fee(shift)
			}))
		
			let total = 0
			for(const cost of costs)
				total += cost

			return total
		}
	}
}

const forecast = async (frm) => {
	
	const calc = {
		costs: {
			staff: async (shifts) => {
				return utils.shift.sum(shifts)
			},
			drinks: (guests, bar_per_capita, margin) => {
				return guests * bar_per_capita / margin
			}
		},
		revenue: {
			entrance: (start, end, entrances, guests) => {
				return utils.entrance.project(start, end, entrances, guests)
			},
			bar: (guests, bar_per_capita) => {
				return guests * bar_per_capita
			}
		}
	}

	const {
		name, 
		start,
		end,
		entrances,
		forecast_booking_factor, 
		forecast_bar_per_capita, 
		forecast_estimated_guests,
		forecast_margin,
		forecast_shift_template,
		forecast_use_shift_plan,
	} = frm.doc

	const shifts = await frappe.db.get_list('Shift', {
		filters: forecast_use_shift_plan ? {event: name} : {template: forecast_shift_template},
		fields: ['job', 'start', 'end'],
	})

	const revenues = {
		entrance: calc.revenue.entrance(start, end, entrances, forecast_estimated_guests),
		bar: calc.revenue.bar(forecast_estimated_guests, forecast_bar_per_capita),
	}

	const costs = {
		booking: revenues.entrance * forecast_booking_factor,
		drinks: calc.costs.drinks(forecast_estimated_guests, forecast_bar_per_capita, forecast_margin),
		staff: await calc.costs.staff(shifts),
		venue: 0,
	}

	const costs_total = costs.booking + costs.staff + costs.drinks + costs.venue
	const revenues_total = revenues.entrance + revenues.bar
	const effective_entrance = utils.entrance.effective_price(start, end, entrances)

	const general = {
		effective_entrance: effective_entrance,
		break_even: Math.round(costs_total / (effective_entrance + forecast_bar_per_capita))
	}

	frm.set_value('forecast_effective_entrance', general.effective_entrance)
	frm.set_value('forecast_break_even', general.break_even)
	frm.set_value('forecast_revenue_entrance', revenues.entrance)
	frm.set_value('forecast_revenue_bar', revenues.bar)
	frm.set_value('forecast_costs_booking', costs.booking)
	frm.set_value('forecast_costs_staff', costs.staff)
	frm.set_value('forecast_costs_drinks', costs.drinks)
	frm.set_value('forecast_balance_costs', costs_total)
	frm.set_value('forecast_balance_revenues', revenues_total)
	frm.set_value('forecast_balance_total', revenues_total - costs_total)
}

const balance = async (frm) => {

	const calc = {
		data: {
			bar_per_capita: (entrances, revenue_bar) => {
				const guests_total = utils.entrance.count_guests(entrances)
				return (guests_total === 0) ? 0 : revenue_bar / guests_total
			}
		},
		costs: {
			shift: async (shifts) => {
				return await utils.shift.sum(shifts)
			},
			booking: (bookings) => {
				return utils.booking.sum(bookings)
			},
			drinks: () => 123,
			renting: (rentings) => {
				return utils.renting.sum(rentings)
			},
			promo: (promos) => {
				return utils.promo.sum(promos)
			},
			kitchen: (kitchen_costs) => {
				return utils.kitchen.sum(kitchen_costs)
			},
			uncategorized: (uncategorized_costs) => {
				return utils.uncategorized.sum(uncategorized_costs)
			},
		},
		revenue: {
			entrance: (entrances) => {
				return utils.entrance.sum(entrances)
			},
			bar: () => {
				return 123
			},
		}
	}

	const {
		entrances,
		name
	} = frm.doc

	const shifts = await frappe.db.get_list('Shift', {
		filters: {event: name},
		fields: ['job', 'start', 'end'],
	})

	const bookings = await frappe.db.get_list('Booking', {
		filters: {event: name},
		fields: [
			'artist_fee',
			'include_booker',
			'booking_fee',
			'include_hotel',
			'hotel_fee'
		],
	})

	const revenue = {
		entrance: calc.revenue.entrance(entrances),
		bar: calc.revenue.bar()
	}

	const costs = {
		booking: calc.costs.booking(bookings),
		drinks: calc.costs.drinks(),
		staff: await calc.costs.shift(shifts)
	}

	const data = {
		bar_per_capita: calc.data.bar_per_capita(entrances, 10000)
	}

	const costs_total = costs.booking + costs.drinks + costs.staff
	const revenue_total = revenue.bar + revenue.entrance

	frm.set_value('balance_bar_per_capita', data.bar_per_capita)
	frm.set_value('balance_costs_booking', costs.booking)
	frm.set_value('balance_costs_drinks', costs.drinks)
	frm.set_value('balance_costs_staff', costs.staff)
	frm.set_value('balance_revenue_entrance', revenue.entrance)
	frm.set_value('balance_revenue_bar', revenue.bar)
	frm.set_value('balance_costs', costs_total)
	frm.set_value('balance_revenue', revenue_total)
	frm.set_value('balance_total', revenue_total - costs_total)
}

const set_parameter_template_values = async (frm, parameters) => {
	if(!parameters)
		return

	const {booking_factor, bar_per_capita, margin, include_heating} = parameters
	frm.set_value('forecast_booking_factor', booking_factor)
	frm.set_value('forecast_bar_per_capita', bar_per_capita)
	frm.set_value('forecast_margin', margin)
	frm.set_value('forecast_include_heating', include_heating)
}

frappe.realtime.on('msgprint', (data) => {
	console.log(data)
})

frappe.ui.form.on('Club Event', {
	setup: async (frm) => {
		const default_forecast_parameters = await frappe.db.get_single_value('Default Forecast Parameters', 'forecast_parameters')
		const parameters = await frappe.db.get_doc('Forecast Parameters', default_forecast_parameters)
		set_parameter_template_values(frm, parameters)
	},

	onload: async (frm) => {
		console.log('Add msgprint listener')
		frappe.realtime.on('msgprint', (data) => {
			console.log(data)
		})
	
		await forecast(frm)
		await balance(frm)
	},

	forecast_estimated_guests: async (frm) => {
		await forecast(frm)
	},

	forecast_load_parameter_template: (frm) => {
		const dialog = new frappe.ui.Dialog({
			title: 'Parameter Template',
			fields: [
				{
					label: 'Parameter Template',
					fieldname: 'parameter_template',
					fieldtype: 'Link',
					options: 'Forecast Parameters'
				}
			],
			primary_action_label: 'Load',
			primary_action: async (values) => {
				const {parameter_template} = values
				if(!parameter_template)
					return

				const parameters = await frappe.db.get_doc('Forecast Parameters', parameter_template)
				set_parameter_template_values(frm, parameters)
				dialog.hide()
			}
		})
	
		dialog.show()
	},

	forecast_booking_factor: async (frm) => {
		await forecast(frm)
	},

	forecast_bar_per_capita: async (frm) => {
		await forecast(frm)
	},

	forecast_margin: async (frm) => {
		await forecast(frm)
	},

	forecast_include_heating: async (frm) => {
		await forecast(frm)
	},

	forecast_use_shift_plan: async (frm) => {
		await forecast(frm)
	},

	forecast_shift_template: async (frm) => {
		await forecast(frm)
	},

	validate: (frm) => {
		const {
			areas,
			end,
			entrances,
			start,
		} = frm.doc

		const in_range = (a, b, v) => {
			const {str_to_user} = frappe.datetime
			const ad = str_to_user(a)
			const bd = str_to_user(b)
			const vd = str_to_user(v)
			return (ad <= vd) && (bd >= vd)
		}

		areas.forEach(area => {
			if(!in_range(start, end, area.start) || !in_range(start, end, area.end)) {
				frappe.msgprint('Area opening needs to be during club opening.')
				frappe.validated = false
			}
		})

		entrances.forEach(entrance => {
			if(!in_range(start, end, entrance.start)) {
				frappe.msgprint('Entrance start time needs to be during club opening.')
				frappe.validated = false
			}
		})
	}
});
