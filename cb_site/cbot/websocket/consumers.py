from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from partialjson import JSONParser

import json
import asyncio

from typing import Any

from ..services.api_logic import ApiLogic
from ..services.data_caching import DataCache

from .. import models as mdls

class ChatConsumer(AsyncWebsocketConsumer):

    #################################################################### base methods

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        # init chat session id as an invalid number: chat session ids are from [0, 2^32) and are unique
        self.current_chat_session_id: int = -1
        # a task handler to handle concurrent tasks
        self.current_task: asyncio.Task[None] | None = None 


    async def connect(self) -> None:
        self.current_chat_session_id = await database_sync_to_async(
            lambda: DataCache(self.scope["session"]).get_current_cookie_session().current_chat_session.id #type: ignore
        )()
        await self.accept()

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        if (text_data is None):
            return
        
        # check if a task is running actively
        if (not self.current_task is None and not self.current_task.done()):
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                print("task cancelled")

        # serialize our text
        message: str = self.get_message(text_data)
        # now generate a response using create task, this allows us to have an async method that runs concurrently
        # allowing receive to receive other messages (django channels runs sequentially (essentially causing
        # a queue; which is not what we want), that's why we do this)
        self.current_task = asyncio.create_task(self.generate_response(message))

    async def disconnect(self, code: int) -> None:
        # when we disconnect, make sure to store our chat session into our context 
        await self._cache_current_chat()
    
    #################################################################### misc methods

    # decorators to make our sync methods to async
    # storage of a message pair (after a successful request)
    @database_sync_to_async
    def _store_message_pair(self, message: str, response: dict[str, str | int]) -> None:
        dc = DataCache(self.scope["session"]) #type: ignore
        dc.store_to_session_context(message, response, self.current_chat_session_id)

    # save our current chat session and unlink it from our cookie session
    @database_sync_to_async
    def _cache_current_chat(self) -> None:
        if (self.current_chat_session_id == -1):
            return

        dc = DataCache(self.scope["session"]) #type: ignore

        current_chat: mdls.ChatSession | None = dc.get_current_cookie_session().current_chat_session

        # so in the case of sudden refreshes or disconnects, this helps us safely remove store chat sessions
        # into the overall cookie
        if (not current_chat is None and self.current_chat_session_id == current_chat.id):
            dc.cache_chat_session()
        else:
            dc.cache_chat_session_by_id(self.current_chat_session_id)
        
    # serialize incoming json data and return our message
    def get_message(self, text_data: str) -> str:
        # deserialize the user's input
        json_deserialized: Any = json.loads(text_data)
        return json_deserialized["message"]

    # generate a response from our message
    async def generate_response(self, message: str) -> None:
        al = ApiLogic()
        # setting up our variables to get a response
        jparser = JSONParser()
        prev_response_len: int = 0

        # now generate our response stream
        try:
            async for chunk in al.generate_response_stream_openai(al.openai_model, message):
                # check if we can access the json objects
                if (not hasattr(chunk, "snapshot") and not hasattr(chunk, "text")):
                    continue

                parsed_response: dict[str, str | int] | None = (jparser.parse(chunk.snapshot) #type: ignore
                                                                if hasattr(chunk, "snapshot")
                                                                else jparser.parse(chunk.text)) #type: ignore
                is_final_chunk: bool = al.is_last_chunk_openai(chunk)

                # if our parsed response is valid + the response key exists + "response" key is not null
                if (not parsed_response is None 
                    and "response" in parsed_response
                    and not parsed_response["response"] is None
                    and not len(parsed_response["response"]) < prev_response_len): #type: ignore (only in async sometimes the response obj is literally empty)
                    # send our message
                    await self.send(json.dumps(
                        {
                            "message": parsed_response["response"][prev_response_len:], #type: ignore
                            "is_finished": is_final_chunk
                        }
                    ))

                    # check if the request is completed, if so store the text in our database
                    if (is_final_chunk):
                        await self._store_message_pair(message, parsed_response) #type: ignore
                    # since we want only the new parts of the text (since we're appending),
                    # we have to do this
                    prev_response_len = len(parsed_response["response"]) #type: ignore
                # NOTE: super important, actually allows websocket messages to be sent or else
                # we'll be iterating through each chunk faster than what the websocket messages can send
                # causing basically to do the same thing as sending the entire response body a minor delay 
                # like 0.001 sec works, we just need to "pause" the coroutine
                # await asyncio.sleep(0.001)
        except Exception as e: 
            await self.send(text_data=json.dumps({
                    "message": str(e),
                    "is_finished": True
                }))
