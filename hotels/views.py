from django.http import HttpResponse

def hotel_list_view(request):
    return HttpResponse("Hotels list")

def hotel_detail_view(request, slug):
    return HttpResponse(f"Hotel detail: {slug}")

def room_detail_view(request, pk):
    return HttpResponse(f"Room detail: {pk}")
