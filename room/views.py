from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum, F, DecimalField
from django.db import models
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail

from .models import House, Room, PaymentHistory, Tenant
from .forms import PaymentHistoryForm, TenantForm, TenantDocumentForm, RoomForm


def landing_view(request):
    if request.user.is_authenticated:
        return redirect("room:dashboard")
    return render(request, "landing.html")


def _send_tenant_test_email(request, tenant):
    if not tenant.email:
        return False

    subject = "Tenant email verification"
    message = (
        f"Hi {tenant.name},\n\n"
        "This is a test email to verify billing delivery for your room.\n"
        f"Room: {tenant.room}\n"
        "If you received this, your email is verified."
    )
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [tenant.email])
        tenant.email_verified = True
        tenant.save(update_fields=["email_verified"])
        messages.success(request, "Test email sent. Tenant email marked as verified.")
        return True
    except Exception:
        tenant.email_verified = False
        tenant.save(update_fields=["email_verified"])
        messages.error(request, "Unable to send test email to tenant.")
        return False


def _send_bill_email(request, payment, custom_message=None):
    tenant = getattr(payment.room, "tenant", None)
    if not tenant or not tenant.email or not tenant.email_verified:
        messages.info(request, "Bill saved. Tenant email is missing or unverified; no email sent.")
        return False

    subject = f"Bill for {payment.room} - {payment.billing_month}"
    if custom_message:
        message = custom_message
    else:
        message = (
            f"Hi {tenant.name},\n\n"
            "Here is your billing summary:\n"
            f"Room: {payment.room}\n"
            f"Billing month: {payment.billing_month}\n"
            f"Units: {payment.previous_units} -> {payment.current_units}\n"
            f"Electricity: Rs. {payment.electricity}\n"
            f"Rent: Rs. {payment.rent}\n"
            f"Water: Rs. {payment.water}\n"
            f"Waste: Rs. {payment.waste}\n"
            f"Total: Rs. {payment.total}\n\n"
            "Thank you."
        )
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [tenant.email])
        messages.success(request, "Bill email sent to tenant.")
        return True
    except Exception:
        messages.error(request, "Bill saved, but sending email failed.")
        return False


def _build_pending_bills_message(tenant, room, unpaid_payments):
    lines = [
        f"Hi {tenant.name},",
        "",
        "Here is your pending billing summary:",
        f"Room: {room}",
        "",
    ]

    for payment in unpaid_payments:
        lines.extend(
            [
                f"Billing month: {payment.billing_month}",
                f"Units: {payment.previous_units} -> {payment.current_units}",
                f"Electricity: Rs. {payment.electricity}",
                f"Rent: Rs. {payment.rent}",
                f"Water: Rs. {payment.water}",
                f"Waste: Rs. {payment.waste}",
                f"Total: Rs. {payment.total}",
                f"Paid: Rs. {payment.total_paid}",
                f"Status: {payment.status}",
                "",
            ]
        )

    lines.append("Thank you.")
    return "\n".join(lines)


def send_pending_bills_email(request, room_id):
    room = get_object_or_404(
        Room.objects.select_related("house", "tenant"),
        id=room_id,
        house__owner=request.user,
    )
    tenant = getattr(room, "tenant", None)
    if not tenant:
        messages.error(request, "Add a tenant before sending a bill email.")
        return redirect("room:room_detail", room_id=room.id)

    unpaid_payments = PaymentHistory.objects.filter(
        room=room,
        status__in=["Unpaid", "Partially Paid"],
    ).order_by("-created_at", "-billing_month")

    if not unpaid_payments.exists():
        messages.info(request, "No pending bills found.")
        return redirect("room:room_detail", room_id=room.id)

    if request.method == "POST":
        custom_message = request.POST.get("custom_message", "").strip()
        subject = f"Pending bills for {room}"
        body = custom_message or _build_pending_bills_message(tenant, room, unpaid_payments)
        if not tenant.email or not tenant.email_verified:
            messages.info(request, "Tenant email is missing or unverified; no email sent.")
            return redirect("room:room_detail", room_id=room.id)
        try:
            send_mail(subject, body, settings.EMAIL_HOST_USER, [tenant.email])
            messages.success(request, "Pending bills email sent to tenant.")
        except Exception:
            messages.error(request, "Sending pending bills email failed.")
        return redirect("room:room_detail", room_id=room.id)

    message = _build_pending_bills_message(tenant, room, unpaid_payments)
    return render(
        request,
        "room/pending_bills_email.html",
        {
            "room": room,
            "tenant": tenant,
            "message": message,
        },
    )


def dashboard_view(request):
    from django.db.models import Sum, F
    
    houses = House.objects.filter(owner=request.user).annotate(
        rooms_count=Count("room", distinct=True),
        occupied_count=Count("room", filter=Q(room__is_occupied=True), distinct=True),
        vacant_count=Count("room", filter=Q(room__is_occupied=False), distinct=True),
    ).order_by("name")
    
    total_rooms = Room.objects.filter(house__owner=request.user).count()
    occupied_rooms = Room.objects.filter(house__owner=request.user, is_occupied=True).count()
    vacant_rooms = total_rooms - occupied_rooms
    
    # Calculate monthly estimated income
    monthly_income = Tenant.objects.filter(
        room__house__owner=request.user
    ).aggregate(total=Sum('rent_price'))['total'] or 0
    
    # Calculate annual estimated income
    annual_income = monthly_income * 12
    
    # Calculate remaining amount (unpaid payments)
    remaining_amount = PaymentHistory.objects.filter(
        room__house__owner=request.user,
        status='pending'
    ).aggregate(
        total=Sum(F('total') - F('total_paid'), output_field=models.DecimalField())
    )['total'] or 0
    
    recent_payments = PaymentHistory.objects.filter(
        room__house__owner=request.user
    ).select_related("room__house").order_by("-created_at")[:10]
    
    context = {
        "houses": houses,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "vacant_rooms": vacant_rooms,
        "monthly_income": monthly_income,
        "annual_income": annual_income,
        "remaining_amount": remaining_amount,
        "recent_payments": recent_payments,
    }
    return render(request, "room/dashboard.html", context)


def house_view(request):
    houses = (
        House.objects.filter(owner=request.user)
        .annotate(
            rooms_count=Count("room", distinct=True),
            occupied_count=Count("room", filter=Q(room__is_occupied=True), distinct=True),
            vacant_count=Count("room", filter=Q(room__is_occupied=False), distinct=True),
        )
        .order_by("name")
    )
    return render(request, "room/house.html", {"houses": houses})


def room_view(request, house_id):
    house = get_object_or_404(House, id=house_id, owner=request.user)
    rooms = (
        Room.objects.filter(house=house)
        .select_related("house")
        .order_by("room_number")
    )
    return render(request, "room/room.html", {"house": house, "rooms": rooms})


def available_rooms_view(request):
    rooms = (
        Room.objects.filter(house__owner=request.user)
        .select_related("house")
        .order_by("house__name", "room_number")
    )
    return render(request, "room/available_rooms.html", {"rooms": rooms})


def room_detail_view(request, room_id):
    room = get_object_or_404(
        Room.objects.select_related("house"),
        id=room_id,
        house__owner=request.user,
    )
    tenant = getattr(room, "tenant", None)
    documents = tenant.documents.all() if tenant else []
    payments = room.payment_history.order_by("-created_at", "-billing_month")
    unpaid_payments = PaymentHistory.objects.filter(
        room=room,
        status__in=["Unpaid", "Partially Paid"],
    ).order_by("-created_at", "-billing_month")
    latest_payment = payments.first()
    paginator = Paginator(payments, 5)
    page_obj = paginator.get_page(request.GET.get("page"))
    tenant_form = TenantForm(instance=tenant) if tenant else None

    context = {
        "room": room,
        "tenant": tenant,
        "documents": documents,
        "page_obj": page_obj,
        "tenant_form": tenant_form,
        "latest_payment": latest_payment,
        "unpaid_payments": unpaid_payments,
    }
    return render(request, "room/roomDetail.html", context)


def add_tenant(request, room_id):
    room = get_object_or_404(
        Room.objects.select_related("house"),
        id=room_id,
        house__owner=request.user,
    )

    if hasattr(room, "tenant"):
        messages.info(request, "This room already has a tenant.")
        return redirect("room:room_detail", room_id=room.id)

    if request.method == "POST":
        form = TenantForm(request.POST)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.room = room
            tenant.save()
            room.is_occupied = True
            room.save(update_fields=["is_occupied"])
            if tenant.email:
                _send_tenant_test_email(request, tenant)
            messages.success(request, "Tenant assigned successfully.")
            return redirect("room:room_detail", room_id=room.id)
    else:
        form = TenantForm()

    return render(
        request,
        "room/tenant_form.html",
        {
            "form": form,
            "room": room,
            "page_title": "Assign tenant",
            "page_subtitle": "Add tenant details for this room.",
            "submit_label": "Assign",
        },
    )


def update_tenant(request, room_id):
    room = get_object_or_404(
        Room.objects.select_related("house", "tenant"),
        id=room_id,
        house__owner=request.user,
    )
    tenant = getattr(room, "tenant", None)
    if not tenant:
        return redirect("room:add_tenant", room_id=room.id)

    if request.method == "POST":
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            email_changed = "email" in form.changed_data
            tenant = form.save()
            if email_changed:
                tenant.email_verified = False
                tenant.save(update_fields=["email_verified"])
                if tenant.email:
                    _send_tenant_test_email(request, tenant)
            messages.success(request, "Tenant updated successfully.")
    return redirect("room:room_detail", room_id=room.id)


def upload_document(request, room_id):
    room = get_object_or_404(
        Room.objects.select_related("house", "tenant"),
        id=room_id,
        house__owner=request.user,
    )
    tenant = getattr(room, "tenant", None)
    if not tenant:
        messages.error(request, "Assign a tenant before uploading documents.")
        return redirect("room:room_detail", room_id=room.id)

    if request.method == "POST":
        form = TenantDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.tenant = tenant
            document.save()
            messages.success(request, "Document uploaded successfully.")
            return redirect("room:room_detail", room_id=room.id)
    else:
        form = TenantDocumentForm()

    return render(
        request,
        "room/document_form.html",
        {
            "form": form,
            "room": room,
            "page_title": "Upload document",
            "page_subtitle": "Attach a document to this tenant.",
            "submit_label": "Upload",
        },
    )


def add_payment(request, room_id):
    room = get_object_or_404(
        Room.objects.select_related("house", "tenant"),
        id=room_id,
        house__owner=request.user,
    )

    if not hasattr(room, "tenant"):
        messages.error(request, "Add a tenant before creating a bill.")
        return redirect("room:room_detail", room_id=room.id)

    last_payment = (
        PaymentHistory.objects.filter(room=room)
        .order_by("-billing_month", "-created_at")
        .first()
    )
    previous_units = last_payment.current_units if last_payment else 0

    if request.method == "POST":
        form = PaymentHistoryForm(request.POST)
        form.instance.previous_units = previous_units
        if form.is_valid():
            payment = form.save(commit=False)
            payment.room = room
            payment.save()
            messages.success(request, "Bill added successfully.")
            _send_bill_email(request, payment)
            return redirect("room:room_detail", room_id=room.id)
    else:
        form = PaymentHistoryForm()

    return render(
        request,
        "room/payment_form.html",
        {
            "form": form,
            "room": room,
            "page_title": "Add bill",
            "page_subtitle": "Create a new billing record for this room.",
            "submit_label": "Create",
            "previous_units": previous_units,
        },
    )


def send_bill_email(request, payment_id):
    payment = get_object_or_404(
        PaymentHistory.objects.select_related("room__house", "room__tenant"),
        id=payment_id,
        room__house__owner=request.user,
    )

    custom_message = None
    if request.method == "POST":
        custom_message = request.POST.get("custom_message", "").strip() or None

    _send_bill_email(request, payment, custom_message=custom_message)
    return redirect("room:room_detail", room_id=payment.room.id)


def edit_payment(request, payment_id):
    payment = get_object_or_404(
        PaymentHistory.objects.select_related("room__house", "room__tenant"),
        id=payment_id,
        room__house__owner=request.user,
    )

    if request.method == "POST":
        form = PaymentHistoryForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            if "current_units" in form.changed_data:
                tenant = getattr(payment.room, "tenant", None)
                if tenant:
                    payment.electricity = (
                        payment.current_units - payment.previous_units
                    ) * tenant.electricity_price_per_unit
                    payment.water = tenant.water_price
                    payment.rent = tenant.rent_price
                    payment.waste = tenant.waste_price
            payment.save()
            messages.success(request, "Payment updated successfully.")
            return redirect("room:room_detail", room_id=payment.room.id)
    else:
        form = PaymentHistoryForm(instance=payment)

    return render(
        request,
        "room/payment_form.html",
        {
            "form": form,
            "room": payment.room,
            "payment": payment,
            "page_title": "Edit payment",
            "page_subtitle": "Update billing details for this record.",
            "submit_label": "Save",
        },
    )


def delete_payment(request, payment_id):
    payment = get_object_or_404(
        PaymentHistory.objects.select_related("room__house"),
        id=payment_id,
        room__house__owner=request.user,
    )
    room_id = payment.room.id

    if request.method == "POST":
        payment.delete()
        messages.success(request, "Payment deleted successfully.")
        return redirect("room:room_detail", room_id=room_id)

    return redirect("room:room_detail", room_id=room_id)


def view_payment(request, payment_id):
    payment = get_object_or_404(
        PaymentHistory.objects.select_related("room__house", "room__tenant"),
        id=payment_id,
        room__house__owner=request.user,
    )

    return render(
        request,
        "room/payment_detail.html",
        {"payment": payment, "room": payment.room},
    )


def add_room(request, house_id):
    house = get_object_or_404(House, id=house_id, owner=request.user)
    
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.house = house
            room.save()
            messages.success(request, f"Room {room.room_number} added successfully.")
            return redirect("room:house_rooms", house_id=house.id)
    else:
        form = RoomForm()
    
    return render(
        request,
        "room/room_form.html",
        {
            "form": form,
            "house": house,
            "page_title": "Add room",
            "page_subtitle": f"Add a new room to {house.name}",
            "submit_label": "Add room",
        },
    )


def add_house(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            House.objects.create(name=name, owner=request.user)
            messages.success(request, f"House '{name}' added successfully!")
            return redirect("room:houses")
        else:
            messages.error(request, "House name is required.")
    return redirect("room:houses")


def toggle_house_status(request, house_id):
    if request.method == "POST":
        house = get_object_or_404(House, id=house_id, owner=request.user)
        house.is_active = not house.is_active
        house.save()
        return JsonResponse({"success": True, "is_active": house.is_active})
    return JsonResponse({"success": False}, status=400)
