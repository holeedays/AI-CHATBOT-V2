from channels.generic.websocket import AsyncWebsocketConsumer
from partialjson import JSONParser

import json
import asyncio

from ..services.logic import CB

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        await self.accept()

    async def receive(self, text_data: str | None=None, bytes_data: bytes | None =None) -> None:
        if (text_data is None):
            return
        
        json_deserialized = json.loads(text_data)
        message = json_deserialized["message"]

        # process message here 
        cb = CB()
        cb.gemini_model = "gemini-2.5-flash"
        jparser = JSONParser()
        prev_response = ""
        accumulated_response = ""
        response = ""

        for chunk in cb.generate_response_stream_gemini(cb.gemini_model, message):
            try:
                accumulated_response += chunk.candidates[0].content.parts[0].text #type: ignore
                accumulated_response_parsed: dict[str, str | int] | None = jparser.parse(accumulated_response) #type: ignore

                if (not accumulated_response_parsed is None):
                    response: str = accumulated_response_parsed["response"]

                    await self.send(text_data=json.dumps({
                        "message": response[len(prev_response):],
                        "is_finished": cb.is_last_chunk_gemini(chunk)
                    }))

                    prev_response = response

                # NOTE: THIS IS EXTREMELY IMPORTANT, self.send() acts like queue rather than an execution due to the nature
                # of python's single thread behavior... manually induce a yield statement so that we can exit the generator
                # momentarily to actually push the data from queue out
                await asyncio.sleep(0.3)
            except Exception as e:
                print(e)
                pass

    async def disconnect(self, code: int) -> None:
        pass