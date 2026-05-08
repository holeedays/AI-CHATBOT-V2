from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from .services.data_caching import DataCache

# Create your views here.
@ensure_csrf_cookie
def home_pg(request: HttpRequest) -> HttpResponse:

    # since cookies only get written during a request/response cycle (not websocket it seems...)
    # we'll create a new session over here versus in our websocket consumers.py
    dc = DataCache(request.session) #type: ignore

    dc.generate_cookie()
    current_cookie = dc.get_current_cookie_session()

    # this is a check to see if our context has been compressed successfully; if it doesn't, the websocket
    # just disconnects and the chat is just broken
    if (current_cookie.is_compressing_context):
        return render(request, "cbot/compressing.html", {
            "status_url": reverse("compression status"),
            "chat_url": reverse("home page"),
            "use_plain_font": current_cookie.use_plain_font,
        })

    dc.generate_chat_session()

    return render(request, "cbot/index.html", {
        "use_plain_font": current_cookie.use_plain_font,
    })

# this is our compression status check page
def compression_status(request: HttpRequest) -> JsonResponse:
    dc = DataCache(request.session) #type: ignore
    dc.generate_cookie()
    current_cookie = dc.get_current_cookie_session()

    return JsonResponse({
        "is_compressing_context": current_cookie.is_compressing_context,
    })

# an intermediary page to check what our font preference is
def font_preference(request: HttpRequest) -> JsonResponse:
    if (request.method != "POST"):
        return JsonResponse({"ok": False}, status=405)

    use_plain_font: bool = request.POST.get("use_plain_font", "false").lower() == "true"

    dc = DataCache(request.session) #type: ignore
    dc.generate_cookie()
    dc.set_cookie_font_preference(use_plain_font)

    # this is just to return something even though our AJAX request doesn't actually use the value anyways
    return JsonResponse({
        "ok": True
    })
