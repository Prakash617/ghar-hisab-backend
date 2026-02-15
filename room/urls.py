from django.urls import path
from .views import (
	landing_view,
	dashboard_view,
	house_view,
	room_view,
	available_rooms_view,
	room_detail_view,
	add_house,
	add_room,
	toggle_house_status,
	edit_payment,
	delete_payment,
	view_payment,
	add_payment,
	send_bill_email,
	send_pending_bills_email,
	add_tenant,
	update_tenant,
	upload_document,
)

app_name = "room"

urlpatterns = [
	path("", landing_view, name="landing"),
	path("dashboard/", dashboard_view, name="dashboard"),
	path("rooms/available/", available_rooms_view, name="available_rooms"),
	path("houses/", house_view, name="houses"),
	path("houses/add/", add_house, name="add_house"),
	path("houses/<int:house_id>/toggle/", toggle_house_status, name="toggle_house_status"),
	path("houses/<int:house_id>/rooms/", room_view, name="house_rooms"),
	path("houses/<int:house_id>/rooms/add/", add_room, name="add_room"),
	path("rooms/<int:room_id>/", room_detail_view, name="room_detail"),
	path("rooms/<int:room_id>/tenant/add/", add_tenant, name="add_tenant"),
	path("rooms/<int:room_id>/tenant/update/", update_tenant, name="update_tenant"),
	path("rooms/<int:room_id>/documents/add/", upload_document, name="upload_document"),
	path("rooms/<int:room_id>/payments/add/", add_payment, name="add_payment"),
	path("rooms/<int:room_id>/payments/pending/email/", send_pending_bills_email, name="send_pending_bills_email"),
	path("payments/<int:payment_id>/", view_payment, name="view_payment"),
	path("payments/<int:payment_id>/edit/", edit_payment, name="edit_payment"),
	path("payments/<int:payment_id>/send/", send_bill_email, name="send_bill_email"),
	path("payments/<int:payment_id>/delete/", delete_payment, name="delete_payment"),
]
