frappe.views.calendar["Club Event"] = {
  field_map: {
      "start": "start",
      "end": "end",
      "id": "name",
      "title": "event_name",
  },
  get_events_method: "club.club.doctype.club_event.club_event.get_events"
}