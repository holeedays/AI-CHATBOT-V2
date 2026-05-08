from django.db import models

# Create your models here.

# data tied to per session 
class ChatSession(models.Model):
    # this is the unique identifier for our chatsessions, the inbuilt id is still the primary key so 
    # the models stay consistent
    created_at = models.DateTimeField(auto_now_add=True)
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
    # this field is a flag to determine whether the user should be redirected to the chatbot page or a waiting page
    # as we wait for the contxt to compress
    is_compressing_context = models.BooleanField(default=False)
    # this is a frontend thing, just saves the state of our current font throughout the cookie's lifespan
    use_plain_font = models.BooleanField(default=False)
    # these hold the continuum of our conversation state, so users can come back and immediately resume wheree
    # they left off
    reference_doc: models.ForeignKey["Document"] | models.ForeignKey[None] = models.ForeignKey(
        "Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rd"
        )
    # these parts are used when the reference doc has more than one chunk
    used_chunks_indices = models.JSONField(default=list) #type: ignore
    current_chunk_index_of_reference_doc = models.IntegerField(
        null=True,
        blank=True
    )
    current_chat_session: models.ForeignKey["ChatSession"] | models.ForeignKey[None] = models.ForeignKey(
        "ChatSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cs",
    )

# container for any documents in JSON format
class Document(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, unique=True) # field is optional
    contents = models.JSONField(default=list, unique=True) #type: ignore

    def __str__(self) -> str:
        return self.name
