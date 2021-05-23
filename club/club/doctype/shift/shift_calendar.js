frappe.views.calendar["Shift"] = {
  field_map: {
      "start": "start",
      "end": "end",
      "id": "name",
      "title": "job",
      "allDay": "all_day"
  },
  get_events_method: "club.club.doctype.shift.shift.get_shifts"
}