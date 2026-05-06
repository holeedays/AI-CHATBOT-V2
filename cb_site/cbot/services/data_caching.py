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
    def __init__(self, django_session_obj: Any) -> None:
        self.django_session_obj: SessionBase = django_session_obj

    # get the session/cookie key of our django session
    def _get_session_key(self) -> str:
        session_key = self.django_session_obj.session_key

        if (session_key is None):
            raise Exception("No django session key was found, please create one")

        return session_key
    
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
        # create our chat session or return the current one if it exists
        new_chat: mdls.ChatSession = mdls.ChatSession(context=[], cookie_session=current_cookie)
        new_chat.save()

        # pylance keeps saying I can't set it to an instance of a new chat (in the foreign key in
        # the cookie session model, it only allows None); we'll ignore it
        current_cookie.current_chat_session = new_chat #type: ignore
        current_cookie.save()

        return new_chat

    # end and cache the current session 
    def cache_chat_session(self) -> None:
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

    # cache a specific chat session directly, the chat model could be outside of the current cookie scope
    # much for flexible in this case
    def cache_chat_session_manually(self, chat: mdls.ChatSession) -> None:
        cookie: mdls.CookieSession = chat.cookie_session
        if (chat.context != list()):
            al = ApiLogic()
            compressed_chat_context: list[dict[str, Any]] = al.compress_context(al.gemini_model, chat.context) #type: ignore
            cookie.context.append(compressed_chat_context) #type: ignore
        # also clear the cookie session's refernce to the chat session to make things neater
        if (not cookie.current_chat_session is None and cookie.current_chat_session.id == chat.id):
            cookie.current_chat_session = None #type: ignore
        cookie.save()

    #  compress any chats here, not limited to current chat
    def compress_chat_session(self, chat: mdls.ChatSession) -> None:
        al = ApiLogic()
        chat_context_compressed: list[dict[str, Any]] = al.compress_context(al.gemini_model, 
                                                                            chat.context) #type: ignore
        chat.context = chat_context_compressed
        chat.save()

    # compress any cookies here, not limited to current cookie
    def compress_cookie_session(self, cookie: mdls.CookieSession) -> None:
        al = ApiLogic()
        context_aggregate: list[dict[str, Any]] = list()
        for chat_context in cookie.context: #type: ignore
            context_aggregate += chat_context #type: ignore

        compressed_cookie_context: list[dict[str, Any]] = al.compress_context(al.gemini_model, context_aggregate) #type: ignore
        cookie.context = [compressed_cookie_context]
        cookie.save()

    # store a user and response pair into our chat context
    def store_to_chat_context(self, user_input: str, response: dict[str, Any], chat_session_id: int | None = None) -> None:

        if (chat_session_id is None):
            current_cookie: mdls.CookieSession = self.get_current_cookie_session()
            current_chat: mdls.ChatSession | None = current_cookie.current_chat_session
        else:
            current_chat = mdls.ChatSession.objects.filter(id=chat_session_id).first()

        # if the chat doesn't exist, create a new one
        if (current_chat is None):
            current_chat = self.generate_chat_session()
    
        current_chat.context.append({"user": user_input, "system": response}) #type: ignore
        current_chat.save() #type: ignore

    def change_reference_doc_of_cookie(self, new_reference_doc: mdls.Document | None, cookie: mdls.CookieSession) -> None:
        cookie.reference_doc = new_reference_doc
        cookie.used_chunks_indices = list()
        cookie.current_chunk_index_of_reference_doc = None
        cookie.save()

    def change_chunk_index_of_cookie(self, new_chunk_index: int, cookie: mdls.CookieSession):
        if (not cookie.current_chunk_index_of_reference_doc is None):
            cookie.used_chunks_indices.append(cookie.current_chunk_index_of_reference_doc)
        cookie.current_chunk_index_of_reference_doc = new_chunk_index
        cookie.save()

    def get_chats(self, **attributes: Any) -> list[mdls.ChatSession]:
        return list(mdls.ChatSession.objects.filter(**attributes).all())
    
    def get_cookies(self, **attributes: Any) -> list[mdls.CookieSession]:
        return list(mdls.CookieSession.objects.filter(**attributes).all())

    def get_documents(self, **attributes: Any) -> list[mdls.Document]:
        return list(mdls.Document.objects.filter(**attributes).all())
