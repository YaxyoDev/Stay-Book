from django.http import HttpResponse

def booking_list_view(request):
    return HttpResponse("Booking list")

def booking_create_view(request, room_id):
    return HttpResponse(f"Booking create for room {room_id}")

def booking_detail_view(request, pk):
    return HttpResponse(f"Booking detail {pk}")

def booking_cancel_view(request, pk):
    return HttpResponse(f"Booking cancel {pk}")
