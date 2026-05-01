from django.db import models

# Create your models here.

# data tied to per session 
class ChatSession(models.Model):
    # this id is a unique identifier that we will use in our websocket
    id = models.IntegerField(unique=True, primary_key=True)
    # instantiates our context as list by default, since the history is sequential;
    context = models.JSONField(default=list) #type: ignore
    cookie_session: models.ForeignKey["CookieSession"] = models.ForeignKey(
        "CookieSession", 
        on_delete=models.CASCADE,
        related_name="chat_sessions")

# context tied to per cookie; we don't need a separate "user" query obj rn since cookie has a unique id
class CookieSession(models.Model):
    # this id is going to be equal to the django session key (since this and the session are representing 
    # the same obj)
    id = models.CharField(max_length=40, unique=True, primary_key=True)
    # instantiates our context as list by default, since the history is sequential;
    # think of this context as a refresher of previous convos
    context = models.JSONField(default=list) #type: ignore

    current_chat_session: models.ForeignKey["ChatSession"] | models.ForeignKey[None] = models.ForeignKey(
        "ChatSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

