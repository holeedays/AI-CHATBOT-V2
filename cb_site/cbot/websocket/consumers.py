from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

import asyncio

from ..services.data_caching import DataCache
from ..services.chat_logic import ChatLogic

from .. import models as mdls

class ChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        # init a reference to the unique identifier of the chat session
        self.current_chat_id: int = -1
        # a task handler to handle concurrent tasks
        self.current_task: asyncio.Task[None] | None = None 
        self.cl = ChatLogic(self)

        self.receive_lock = asyncio.Lock()

    #################################################################### base methods

    async def connect(self) -> None:
        self.current_chat_id = await self._get_or_create_current_chat_id()
        await self.accept()
        self.current_task = asyncio.create_task(self.cl.setup())

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        async with self.receive_lock:
            if (text_data is None):
                return
            
            # check if a task is running actively
            if (not self.current_task is None and not self.current_task.done()):
                self.current_task.cancel()
                try:
                    await self.current_task
                except (asyncio.CancelledError, Exception):
                    pass

            self.current_task = asyncio.create_task(self.cl.update(text_data))

    async def disconnect(self, code: int) -> None:
        if (not self.current_task is None and not self.current_task.done()):
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                print("task cancelled")

        # when we disconnect, make sure to store our chat session into our context 
        await self._cache_current_chat()
        await self._check_for_cookie_context_compression()

        print("hello")
    
    #################################################################### misc methods

    # get the current chat or make one if it doesn't exist
    @database_sync_to_async
    def _get_or_create_current_chat_id(self) -> int:
        dc = DataCache(self.scope["session"]) #type: ignore
        current_cookie: mdls.CookieSession = dc.get_current_cookie_session()
        current_chat: mdls.ChatSession | None = current_cookie.current_chat_session

        if (current_chat is None):
            current_chat = dc.generate_chat_session()

        return current_chat.id #type: ignore
    
    # save our current chat session and unlink it from our cookie session
    @database_sync_to_async
    def _cache_current_chat(self) -> None:
        if (self.current_chat_id == -1):
            return
        dc = DataCache(self.scope["session"]) #type: ignore
        current_cookie: mdls.CookieSession = dc.get_current_cookie_session()
        current_chat: mdls.ChatSession | None = current_cookie.current_chat_session

        # in the case of sudden refreshes or disconnects, this helps us safely remove and store chat sessions
        # into the overall cookie
        if (not current_chat is None and self.current_chat_id == current_chat.id): #type: ignore
            dc.cache_chat_session()
        else:
            chat_session: list[mdls.ChatSession] = dc.get_chats(id=self.current_chat_id)
            if (chat_session != list()):
                dc.cache_chat_session_manually(chat_session[0])

    # just an occassional check if cookie compression is needed
    async def _check_for_cookie_context_compression(self):
        current_chat, past_chats, current_cookie = await self.cl.get_all_relevant_chats_cookies() #type: ignore
        await self.cl.check_for_context_compression(current_cookie)
    
