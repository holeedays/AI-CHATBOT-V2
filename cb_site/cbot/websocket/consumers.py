from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

import asyncio

from ..services.data_caching import DataCache
from ..services.chat_logic import ChatLogic

from .. import models as mdls

# set this asyncio queue here to avoid being dereferenced when the consumer disconnects
ACTIVE_DISCONNECT_CLEANUPS: set[asyncio.Task[None]] = set()

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
        # Treat an active websocket session as "in compression/transition" until disconnect cleanup finishes.
        self.current_chat_id = await self._get_or_create_current_chat_id()
        await self._set_cookie_context_compression_state(True)
        await self.accept()
        self.current_task = asyncio.create_task(self.cl.setup())

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        # this is just a check to prevent duplicate submit requests from executing by accident
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

        # channels sometimes doesn't wait for the websocket to finish on its own so if we're awaiting too many
        # slow tasks, if the websocket misses the disconnect window passed by channels, django just kills it
        # instead we just allocate this asyncio to handle it in the background (non blocking) so that the websocket
        # can just cancel
        cleanup_task: asyncio.Task[None] = asyncio.create_task(self._finalize_disconnect())
        ACTIVE_DISCONNECT_CLEANUPS.add(cleanup_task)
        cleanup_task.add_done_callback(ACTIVE_DISCONNECT_CLEANUPS.discard)

    #################################################################### misc methods

    # Finish any slow cache/compression work after the websocket has already been allowed to close. 
    async def _finalize_disconnect(self) -> None:
        try:
            # when we disconnect, make sure to store our chat session into our context 
            await self._cache_current_chat()
            # check if we need to compress cookie context and if so, do so
            await self._check_for_cookie_context_compression()
        finally:
            # then clear the flag after all disconnect cleanup work has completed.
            await self._set_cookie_context_compression_state(False)

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
            dc.cache_current_chat_session()
        else:
            chat_session: list[mdls.ChatSession] = dc.get_chats(id=self.current_chat_id)
            if (chat_session != list()):
                dc.cache_chat_session_manually(chat_session[0])

    # run cookie-level compression after caching the active chat session.
    async def _check_for_cookie_context_compression(self):
        _, _, current_cookie = await self.cl.get_all_relevant_chats_cookies() #type: ignore
        await self.cl.check_for_context_compression(current_cookie)

    # set cookie's context compression state so we can later check it on websocket disconnect and redirect
    @database_sync_to_async
    def _set_cookie_context_compression_state(self, is_compressing: bool) -> None:
        # Persist whether this cookie session is still being cleaned up/compressed.
        dc = DataCache(self.scope["session"]) #type: ignore
        dc.set_cookie_context_compression_state(is_compressing)
