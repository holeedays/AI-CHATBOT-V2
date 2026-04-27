from django.db import models

# Create your models here.

# data tied to per session 
class Session(models.Model):
    context = models.JSONField(default=dict, blank=True)
    cookieSession: models.ForeignKey["CookieSession"] = models.ForeignKey("CookieSession", on_delete=models.CASCADE)


# context tied to per cookie; we don't need a separate "user" query obj rn since cookie has a unique id
class CookieSession(models.Model):
    context = models.JSONField(default=dict, blank=True)

