from channels.generic.websocket import AsyncWebsocketConsumer

from .api_logic import ApiLogic
from partialjson import JSONParser
from .ai_outputs import ChatOutput

from typing import Any

import json
import asyncio
import traceback

class ChatGenerator():
    def __init__(self, consumer: AsyncWebsocketConsumer):
        self.consumer = consumer
    
    # processed message holds all relevant metadata while subsidiary documents referes to our footnotes/bibliography
    async def generate_response_outline(self, 
                                         processed_message: dict[str, str | int | bool], 
                                         subsidiary_documents: dict[str, Any]) -> ChatOutput:
        outline_prompt: str = f"""
        User Input: {processed_message["message"]}
        Context: {processed_message["context"]}
        Reference Material: {processed_message["reference_material"]}
        Footnotes: {subsidiary_documents["footnotes"]}
        Image_references: {subsidiary_documents["image_appendix"]}

        You are a professor and you're teaching a lesson using the current reference material. You have that along with 
        the existing context to further enrich the lesson. 

        Don't use all the reference material at once. Instead, go bit by bit. 

        You should write a lesson outline, which addresses the user's input and connects it back to the reference material 
        and context; as well as asks relevant questions for the user to respond to. Make the outline usable for a back
        and forth converation. Also if the user is not saying anything relevant, try to link what they're saying back
        to what the lesson is about. Keep this outline ~250 words max.

        Also add reference footnotes and image references throughout the outline if any exist from the material. 
        If done so, keep the footnotes and the image reference citations at the end with clear indications where 
        it attributes in the outline. Furthermore, include the full bibliographic sources (authors, links, titles, etc) 
        for the end since the user needs to be able to reference the source.
        """

        al = ApiLogic()
        response: ChatOutput | None = al.generate_response_openai(al.openai_model, outline_prompt)
        if (not response is None):
            return response
        else:
            raise Exception("Generating the response outline failed :/")
            
    # generate a response from our message
    async def generate_response_final(self, 
                                      processed_message: dict[str, str | int | bool], 
                                      response_outline: str,
                                      **additional_information: Any) -> dict[str, Any] | Any:
        prompt: str = f"""
        Response Outline: {response_outline}
        Additional Information: {additional_information["footnotes_information"]}
        Image References: {additional_information.get("image_appendix", [])}
        Is new user: {processed_message["is_new_user"]}
        Should greet user: {processed_message["should_greet_user"]}

        You are a professor and you're teaching a lesson given the current response outline. You may also have additional
        information to supplement the outline too; the additional information are links tied to the footnotes mentioned
        in the outline so see if you can add more to the response. 
        
        Also, if there are images/figures mentioned throughout the outline, embed the corresponding image links 
        with the html <img> tag and limit the image to 700x700px max and center it. You can refer to the image references 
        in the end of the outline and in the image reference list to get the correct image link to embed.

        If the "Is new user key" is true, treat the user more formally. If it is false, be more warm and intimate to the user.

        The key "Should greet user" tells you whether you should greet the user or not.

        Also treat the user as if they do not know this material and you're teaching this to them for the first time and 
        that none of these instructions were mentioned to you. 
        
        Dumb hard concepts down and make it understandable for a high school freshman.

        Keep the format of this response same to the format of the outline. This means keeping and putting the full 
        footnote sources and figure citation sources at the bottom (authors, titles, links, pages, etc), keeping the 
        response ~200 words max, and acknowleding the user first and foremost.
        """
        al = ApiLogic()
        # setting up our variables to get a response
        jparser = JSONParser()

        # now generate our response stream
        try:
            last_valid_response: dict[str, Any] = dict()

            async for chunk in al.generate_response_stream_openai(al.openai_model, prompt):
                chunk_text: str | None = None

                if (hasattr(chunk, "text")):
                    chunk_text = chunk.text #type: ignore
                elif (hasattr(chunk, "snapshot")):
                    chunk_text = chunk.snapshot #type: ignore

                if (chunk_text is None):
                    continue

                parsed_response: dict[str, Any] | None = jparser.parse(chunk_text) #type: ignore

                # if our parsed response is valid + the response key exists + "response" key is not null
                if (not parsed_response is None 
                    and "response" in parsed_response
                    and not parsed_response["response"] is None): 
                    
                    last_valid_response = parsed_response 
                    # send our update, always mark as not finished during the stream
                    await self.consumer.send(json.dumps({
                            "message": last_valid_response["response"], #type: ignore
                            "is_finished": False
                        }))   
                
                if (al.is_last_chunk_openai(chunk)):
                    break

            # outside the loop, send the final completion signal with the last known good response
            # we wait a small amount of time to ensure no stray chunks are still being processed
            wait_time: float = 0.25
            await asyncio.sleep(wait_time)

            if (last_valid_response != dict()):
                await self.consumer.send(json.dumps({
                    "message": last_valid_response["response"], #type: ignore
                    "is_finished": True
                }))
            else:
                await self.consumer.send(json.dumps({
                    "message": "", #type: ignore
                    "is_finished": True
                }))
            
            return last_valid_response

        except Exception as e: 
            print(traceback.print_exc())
            await self.consumer.send(json.dumps({
                    "message": str(e),
                    "is_finished": True
                }))

    # just generate a introducing/concluding message to the user during first encounter and conclusion of essay
    # or any other message that we want to send instead of the bot
    async def generate_manual_response(self, 
                                       response: str, 
                                       characters_per_send: int, 
                                       time_between_sends: float) -> None:
        
        loop_len: int = len(response) - len(response) % characters_per_send
        for i in range(0, loop_len, characters_per_send):
            await self.consumer.send(json.dumps({
                "message": response[0:i],
                "is_finished": False
            }))

            await asyncio.sleep(time_between_sends)

        await self.consumer.send(json.dumps({
                "message": response,
                "is_finished": True
            }))

    # generating our greeting response
    async def generate_introduction_greeting_response(self):
        intro_greeting: str = (
            "Hey and welcome to... Beautiful Architectures: An AI Retrospective. Right now this isn't the AI "
            "speaking, it's actually me, the author. I just wanted to thank you for checking out this chatbot I made "
            "that teaches you about the topics I cover in my essay. Be prepared and strap up for this journey and enjoy!"
        )
        chars_per_send: int = 2
        type_time: float = 10/1000
        await self.generate_manual_response(intro_greeting, chars_per_send, type_time)

    # generating a response that greets the users if they have already been introduced (e.g. they aren't new)
    async def generate_familiar_greeting_response(self):
        familiar_greeting: str = (
            "Hey! Welcome back, you can continue the chat where you left off with our little bot friend here."
        )
        chars_per_send: int = 2
        type_time: float = 10/1000
        await self.generate_manual_response(familiar_greeting, chars_per_send, type_time)


    # generating our concluding response
    async def generate_concluding_response(self):
        concluding_statement: str = (
            "Hey, the author back here at it again!. This concludes Beautiful Architectures: An AI Retrospective. "
            "I'm happy that you were somewhat interested and tuned in for the entire length of the essay. I hope you "
            "learned a few things from my essay. Maybe they are insightful, maybe they offer you to think in a different "
            "perspective, maybe it didn't. Regardless, I hope you enjoyed this adventure as much as I had making it.\n\n"
            "If you want to restart the journey and check it out again, just close your browser and access the chatbot again. "
            "Otherwise, any other response from here would probably just give you the same message over and over again. "
            "Anyways, have a great day and I'll see you very soon..."
        )
        chars_per_send: int = 2
        type_time: float = 10/1000
        await self.generate_manual_response(concluding_statement, chars_per_send, type_time)

    # and generate our final response, to cement the message that this is the end of the current chat
    async def generate_secondary_concluding_response(self):
        secondary_concluding_statement: str = (
            "Like I had mentioned earlier, feel free to close your browser (that means closing all tabs) and access this "
            "page again."
        )
        chars_per_send: int = 2
        type_time: float = 10/1000
        await self.generate_manual_response(secondary_concluding_statement, chars_per_send, type_time)
