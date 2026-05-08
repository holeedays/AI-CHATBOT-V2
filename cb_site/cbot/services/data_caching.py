from django.contrib.sessions.backends.base import SessionBase

from .. import models as mdls
from .api_logic import ApiLogic

from typing import Any

# for reference, the structure of a chat session is as follows:
"""
[
    {
    "user": ..., 
    "system": {
                "response": ...,
                "prompt_token_count": ...,
                "ai_token_count": ...,
                etc
                }
    }    
]
"""

class DataCache():
    # django_request_obj should be an HttpRequest-like obj but channels calls it a _LazySession so I'll
    # make the type any and convert it in the constructor
    def __init__(self, django_session_obj: Any = None) -> None:
        self.django_session_obj: SessionBase | None = django_session_obj

    ########################################################################### nonstatic methods (requires a session key)

    # get the session/cookie key of our django session
    def _get_session_key(self) -> str:
        if(not hasattr(self.django_session_obj, "session_key")):
            raise Exception("You can't use this method without accessing a valid session key")
        
        return self.django_session_obj.session_key
    
    # get the current cookie session if any
    def get_current_cookie_session(self) -> mdls.CookieSession:
        current_cookie: mdls.CookieSession | None = mdls.CookieSession.objects.filter(id=self._get_session_key()).first() 
        if (current_cookie is None):
            current_cookie = mdls.CookieSession.objects.create(
                id=self._get_session_key(),
                context=[],
                current_chat_session=None
            )
            current_cookie.save()

        return current_cookie        
        
    # generate our django session/cookie and related database objs
    def generate_cookie(self) -> None:
        # if session does exist, means that this method has been executed before so return
        if (self.django_session_obj.session_key is None):
            # this instantiates a session with a bunch of metadata, including a unique id (called session key)
            # so we don't have to determine that
            self.django_session_obj.create()
            self.django_session_obj.save()

        # initialize our cookie, or not if it already exists
        self.get_current_cookie_session()

    # create a new chat session to save our context in
    def generate_chat_session(self) -> mdls.ChatSession:

        # the idea here is the cookie session has a temporal reference to a chat session (e.g. once the window for the
        # chat is closed, then the cookie session stops directly referncing the chat session BUT the chat session will still
        # be linked to that cookie)
        current_cookie: mdls.CookieSession = self.get_current_cookie_session()
        existing_chat: mdls.ChatSession | None = current_cookie.current_chat_session
        if (not existing_chat is None):
            return existing_chat

        # create our chat session or return the current one if it exists
        new_chat: mdls.ChatSession = mdls.ChatSession(context=[], cookie_session=current_cookie)
        new_chat.save()

        # pylance keeps saying I can't set it to an instance of a new chat (in the foreign key in
        # the cookie session model, it only allows None); we'll ignore it
        current_cookie.current_chat_session = new_chat #type: ignore
        current_cookie.save()

        return new_chat

    # store whether this cookie session should temporarily show the compression holding page.
    def set_cookie_context_compression_state(self, is_compressing: bool) -> None:
        current_cookie: mdls.CookieSession = self.get_current_cookie_session()
        current_cookie.is_compressing_context = is_compressing
        current_cookie.save(update_fields=["is_compressing_context"])

    # store the user's font preference so future page loads can reuse it.
    def set_cookie_font_preference(self, use_plain_font: bool) -> None:
        current_cookie: mdls.CookieSession = self.get_current_cookie_session()
        current_cookie.use_plain_font = use_plain_font
        current_cookie.save(update_fields=["use_plain_font"])

    # end and cache the current session 
    def cache_current_chat_session(self) -> None:
        current_cookie: mdls.CookieSession = self.get_current_cookie_session()
        current_chat: mdls.ChatSession | None = current_cookie.current_chat_session
 
        # same goes here with ignoring the pylance check

        # essentially we're adding the context of the current chat session to the current cookie session
        # and then stop referencing the chat from our current cookie session (it's not destroyed but we stopped
        # referencing it)
        if (not current_chat is None and current_chat.context != list()):
            al = ApiLogic()
            compressed_chat_context: list[dict[str, Any]] = al.compress_context(al.gemini_model, current_chat.context) #type: ignore
            current_cookie.context.append(compressed_chat_context) #type: ignore

            current_cookie.current_chat_session = None #type: ignore
            current_cookie.save()

    # store a user and response pair into our chat context
    def store_to_chat_context(self, user_input: str, response: dict[str, Any], chat_session_id: int | None = None) -> None:

        if (chat_session_id is None):
            current_cookie: mdls.CookieSession = self.get_current_cookie_session()
            current_chat: mdls.ChatSession | None = current_cookie.current_chat_session
        else:
            current_chat = mdls.ChatSession.objects.filter(id=chat_session_id).first()

        # if the chat doesn't exist, create a new one but only if a django session object exists
        if (current_chat is None):
            if (self.django_session_obj is not None):
                current_chat = self.generate_chat_session()
            else:
                raise Exception("Cannot create a new chat session without an active Django session.")
    
        current_chat.context.append({"user": user_input, "system": response}) #type: ignore
        current_chat.save() #type: ignore

    ########################################################################### static methods (does not require a session key)

    @staticmethod
    # cache a specific chat session directly, the chat model could be outside of the current cookie scope
    # much for flexible in this case
    def cache_chat_session_manually(chat: mdls.ChatSession) -> None:
        cookie: mdls.CookieSession = chat.cookie_session
        if (chat.context != list()):
            al = ApiLogic()
            compressed_chat_context: list[dict[str, Any]] = al.compress_context(al.gemini_model, chat.context) #type: ignore
            cookie.context.append(compressed_chat_context) #type: ignore
        # also clear the cookie session's refernce to the chat session to make things neater
        if (not cookie.current_chat_session is None and cookie.current_chat_session.id == chat.id):
            cookie.current_chat_session = None #type: ignore
        cookie.save()

    @staticmethod
    #  compress any chats here, not limited to current chat
    def compress_chat_session(chat: mdls.ChatSession) -> None:
        al = ApiLogic()
        chat_context_compressed: list[dict[str, Any]] = al.compress_context(al.gemini_model, 
                                                                            chat.context) #type: ignore
        chat.context = chat_context_compressed
        chat.save()

    @staticmethod
    # compress any cookies here, not limited to current cookie
    def compress_cookie_session(cookie: mdls.CookieSession) -> None:
        al = ApiLogic()
        context_aggregate: list[dict[str, Any]] = list()
        for chat_context in cookie.context: #type: ignore
            context_aggregate += chat_context #type: ignore

        compressed_cookie_context: list[dict[str, Any]] = al.compress_context(al.gemini_model, context_aggregate) #type: ignore
        cookie.context = [compressed_cookie_context]
        cookie.save()

    @staticmethod
    # change the current doc we're referencing in this specific cookie (or leave it as none)
    def change_reference_doc_of_cookie(new_reference_doc: mdls.Document | None, cookie: mdls.CookieSession) -> None:
        cookie.reference_doc = new_reference_doc
        cookie.used_chunks_indices = list()
        cookie.current_chunk_index_of_reference_doc = None
        cookie.save()

    @staticmethod
    # change the chunk (by index) of the current reference doc of this cookie to a new chunk of that doc
    def change_chunk_index_of_cookie(new_chunk_index: int, cookie: mdls.CookieSession):
        if (not cookie.current_chunk_index_of_reference_doc is None):
            cookie.used_chunks_indices.append(cookie.current_chunk_index_of_reference_doc)
        cookie.current_chunk_index_of_reference_doc = new_chunk_index
        cookie.save()

    @staticmethod
    def remove_cached_cookies(cookies: mdls.CookieSession | list[mdls.CookieSession]):
        if (isinstance(cookies, list)):
            for cookie in cookies:
                cookie.delete()
        else:
            cookies.delete()

    @staticmethod
    def get_chats(**attributes: Any) -> list[mdls.ChatSession]:
        return list(mdls.ChatSession.objects.filter(**attributes).all())
    
    @staticmethod
    def get_cookies(**attributes: Any) -> list[mdls.CookieSession]:
        return list(mdls.CookieSession.objects.filter(**attributes).all())

    @staticmethod
    def get_documents(**attributes: Any) -> list[mdls.Document]:
        return list(mdls.Document.objects.filter(**attributes).all())
