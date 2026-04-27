from django.shortcuts import render
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse

# Create your views here.
def home_pg(request: HttpRequest) -> HttpResponse:

    return render(request, "cbot/index.html")