from django.contrib.sessions.backends.base import SessionBase

from .. import models as mdls
from .api_logic import ApiLogic

from typing import Any
import random

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
    
    # generate a unique, random number for chat session
    def _get_unique_chat_session_id(self) -> int:
        all_chat_session_ids: set[int] = {session.id 
                                          for session 
                                          in mdls.ChatSession.objects.all()}
        # pick a number from 0-32bit uint/64bit int max
        id = random.randint(0, 1<<32 - 1)
        if (id in all_chat_session_ids):
            return self._get_unique_chat_session_id()
        else:
            return id
    
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
    def generate_chat_session(self) -> None:

        # the idea here is the cookie session has a temporal reference to a chat session (e.g. once the window for the
        # chat is closed, then the cookie session stops directly referncing the chat session BUT the chat session will still
        # be linked to that cookie)
        current_cookie: mdls.CookieSession = self.get_current_cookie_session()
        # create our chat session or return the current one if it exists
        new_chat: mdls.ChatSession = mdls.ChatSession(id=self._get_unique_chat_session_id(), 
                                                      context=[], 
                                                      cookie_session=current_cookie)
        new_chat.save()

        # pylance keeps saying I can't set it to an instance of a new chat (in the foreign key in
        # the cookie session model, it only allows None); we'll ignore it
        current_cookie.current_chat_session = new_chat #type: ignore
        current_cookie.save()

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

    # NOTE: this is unbounded from current chat sessions or cookie sessions for max flexibility
    # cache a specific chat session based on their idea
    def cache_chat_session_by_id(self, chat_session_id: int) -> None:

        # btw this hinges on the fact that every chat session id is unique (as specified 
        # in the ChatSession models class)
        chat: mdls.ChatSession | None = mdls.ChatSession.objects.filter(id=chat_session_id,).first()

        if (not chat is None):
            cookie: mdls.CookieSession = chat.cookie_session
            if (chat.context != list()):
                al = ApiLogic()
                compressed_chat_context: list[dict[str, Any]] = al.compress_context(al.gemini_model, chat.context) #type: ignore
                cookie.context.append(compressed_chat_context) #type: ignore
            # also clear the cookie session's refernce to the chat session to make things neater
            if (not cookie.current_chat_session is None and cookie.current_chat_session.id == chat_session_id):
                cookie.current_chat_session = None #type: ignore
            cookie.save()
        else:
            raise Exception("The chat session listed does not exist")

    # store a user and response pair into our chat context
    def store_to_session_context(self, user_input: str, response: dict[str, Any], chat_session_id: int | None = None) -> None:

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

    # getting the current chat session context
    def get_chat_session_context(self) -> list[dict[str, Any]]:

        return self.get_current_cookie_session().current_chat_session.context # type: ignore
  

    # returning the current cookie session context
    def get_cookie_session_context(self) -> list[list[dict[str, Any]]]:
        
        return self.get_current_cookie_session().context #type: ignore
