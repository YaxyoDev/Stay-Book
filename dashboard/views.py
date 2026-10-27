from django.http import HttpResponse

def dashboard_overview(request):
    return HttpResponse("Dashboard overview")

def dashboard_hotels(request):
    return HttpResponse("Dashboard hotels")

def dashboard_rooms(request):
    return HttpResponse("Dashboard rooms")

def dashboard_bookings(request):
    return HttpResponse("Dashboard bookings")
