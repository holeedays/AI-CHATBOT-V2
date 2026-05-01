from django.contrib import admin
from .models import ChatSession, CookieSession

# Register your models here.
admin.site.register(ChatSession)
admin.site.register(CookieSession)