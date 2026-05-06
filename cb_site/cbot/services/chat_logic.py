from .. import models as mdls 

from .api_logic import ApiLogic, ChatOutput
from .data_caching import DataCache
from .doc_rankings import DocRanker
from .web_scraping import WebScraper
from .chat_generations import ChatGenerator

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from typing import Any
from enum import Enum, auto


class EssayPhase(Enum):
    THESIS = auto()
    BODY = auto()
    CONCLUSION = auto()
    RECOUNT = auto()


class ChatLogic():
    def __init__(self, consumer: AsyncWebsocketConsumer, chat_pairs_before_compression: int = 7) -> None:
        self.consumer = consumer
        self.essay_phase = EssayPhase.THESIS
        self.chat_pairs_before_compression = chat_pairs_before_compression

        self.cg = ChatGenerator(consumer)
        self.concluding_statement_made = False

    ############################################################################# sync methods
        
    # serialize incoming json data and return our message
    def _get_message(self, text_data: str) -> str:
        # deserialize the user's input
        json_deserialized: Any = json.loads(text_data)
        return json_deserialized["message"]
    
    # check if the given chat session is exhausted
    def _chat_session_context_exhausted(self, chat: mdls.ChatSession) -> bool:
        if (chat.context == list()):
            return False

        latest_pair: dict[str, Any] = chat.context[-1]
        latest_system: dict[str, Any] = latest_pair.get("system", {})
        latest_misc: dict[str, Any] = latest_system.get("misc", {})

        return bool(latest_misc.get("context_exhausted", False))

    def _any_past_chat_exhausted(self, past_chats: list[mdls.ChatSession]) -> bool:
        for chat in past_chats[::-1]:
            if (self._chat_session_context_exhausted(chat)):
                return True
        return False
    
        # safely get our reference material that the ai will be basing its responses off of
    def _get_reference_material(self, current_cookie: mdls.CookieSession) -> Any:
        current_document: mdls.Document | None = current_cookie.reference_doc
        current_chunk_index: int | None = current_cookie.current_chunk_index_of_reference_doc

        if (current_document is None or current_chunk_index is None):
            return ""
        if (current_chunk_index < 0 or current_chunk_index >= len(current_document.contents)):
            return ""
        
        return current_document.contents[current_chunk_index]
    
       # get the chunk of the document, this assumes that cookie session has a document
    def _get_new_chunk_index(self, cookie: mdls.CookieSession, query: str) -> int | None:
        document: mdls.Document | None = cookie.reference_doc

        if (not document is None):
            doc_dict: dict[str, int] = {document.contents[i]: i for i in range(len(document.contents))}
            used_chunks: set[str] = {document.contents[i] for i in cookie.used_chunks_indices}
            if (not cookie.current_chunk_index_of_reference_doc is None):
                used_chunks.add(document.contents[cookie.current_chunk_index_of_reference_doc])
                
            dr = DocRanker() 
            for chunk, score in dr.order_relevant_docs_RRF(document.contents, query):
                if (not chunk in used_chunks):
                    return doc_dict[chunk]
            
            return None
        else:
            raise Exception("Cookie doesn't have a reference document")
        
    def _get_context_stringified(self, 
                                 models: list[mdls.ChatSession] | 
                                         list[mdls.ChatSession | mdls.CookieSession] | 
                                         mdls.ChatSession | 
                                         mdls.CookieSession) -> str:
        al = ApiLogic()
        context_str: str = ""

        if (isinstance(models, list)):
            for c in models:
                if (isinstance(c, mdls.CookieSession)):
                    for _c in c.context: #type: ignore
                        context_str += al.extract_context_to_str(_c) #type: ignore
                else:
                    context_str += al.extract_context_to_str(c.context) #type: ignore
        elif (isinstance(models, mdls.CookieSession)):
            for c in models.context: #type: ignore
                context_str += al.extract_context_to_str(c) #type: ignore
        else:
            context_str = al.extract_context_to_str(models.context) #type: ignore

        return context_str
    
    ############################################################################# async methods

    # we want to keep the enum consistent among multiple chat sessions, so we gotta infer the current phase
    # of the essay
    @database_sync_to_async
    def _infer_essay_progression(self, 
                                 current_cookie: mdls.CookieSession,
                                 current_chat: mdls.ChatSession,
                                 past_chats: list[mdls.ChatSession]) -> EssayPhase:
        current_document: mdls.Document | None = current_cookie.reference_doc

        if (current_document is None):
            has_existing_context: bool = (
                current_cookie.context != list()
                or current_chat.context != list()
                or any(chat.context != list() for chat in past_chats)
            )
            if (has_existing_context):
                return EssayPhase.RECOUNT
            return EssayPhase.THESIS
        
        if (current_document.name == "ARS Essay Introduction"):
            return EssayPhase.THESIS
        elif (current_document.name == "ARS Essay Body"):
            return EssayPhase.BODY
        elif (current_document.name == "ARS Essay Conclusion"):
            return EssayPhase.CONCLUSION
        else:
            return EssayPhase.RECOUNT

    # decorators to make our sync methods to async
    # storage of a message pair (after a successful request)
    @database_sync_to_async
    def _store_message_pair(self, message: str, response: dict[str, str | int]) -> None:
        dc = DataCache(self.consumer.scope["session"]) #type: ignore
        dc.store_to_chat_context(message, response, self.consumer.current_chat_id)

    # retrieve context from our cookie and chat sessions
    @database_sync_to_async
    def get_all_relevant_chats_cookies(self) -> tuple[mdls.ChatSession, list[mdls.ChatSession], mdls.CookieSession]:
        dc = DataCache(self.consumer.scope["session"]) #type: ignore
        current_cookie: mdls.CookieSession = dc.get_current_cookie_session()
        current_chat: mdls.ChatSession | None = current_cookie.current_chat_session
        pc_q: mdls.models.QuerySet[mdls.ChatSession] = mdls.ChatSession.objects.filter(cookie_session=current_cookie).order_by("created_at")

        if (not current_chat is None):
            pc_q = pc_q.exclude(id=current_chat.id)
        else:
            current_chat = dc.generate_chat_session()

        past_chats: list[mdls.ChatSession] = list(pc_q)

        return (current_chat, past_chats, current_cookie)
    
    # get our footnotes and image appendix
    @database_sync_to_async                     
    def _get_subsidiary_documents(self) -> dict[str, Any]:
        footnotes: mdls.Document | None = mdls.Document.objects.filter(name="ARS Essay Footnotes").first()
        image_appendix: mdls.Document | None = mdls.Document.objects.filter(name="ARS Essay Image Appendix").first()

        return {
            "footnotes": footnotes.contents if (not footnotes is None) else [],
            "image_appendix": image_appendix.contents if (not image_appendix is None) else [],
        }

    # holds all related database change methods
    async def _update_db(self, 
                        current_chat: mdls.ChatSession, 
                        past_chats: list[mdls.ChatSession], 
                        current_cookie: mdls.CookieSession,
                        query: str) -> None:
        await self._update_document_progression(current_chat, past_chats, current_cookie, query)
        await self.check_for_context_compression(current_chat)

    # update our document progression and recertifies it (like checking if our essay phase enum is in
    # the correct position)
    @database_sync_to_async
    def _update_document_progression(self, 
                                    current_chat: mdls.ChatSession, 
                                    past_chats: list[mdls.ChatSession], 
                                    current_cookie: mdls.CookieSession,
                                    query: str):
        dc = DataCache(self.consumer.scope["session"]) #type: ignore
        current_document: mdls.Document | None = current_cookie.reference_doc
        current_or_past_exhausted: bool = (
            self._chat_session_context_exhausted(current_chat)
            or self._any_past_chat_exhausted(past_chats)
        )

        # we're setting the cookie's current document 
        match(self.essay_phase):
            case (EssayPhase.THESIS):
                if (current_document is None):
                    thesis_doc: mdls.Document = dc.get_documents(name="ARS Essay Introduction")[0]
                    dc.change_reference_doc_of_cookie(thesis_doc, current_cookie)
                    dc.change_chunk_index_of_cookie(0, current_cookie)
                    return

                if (current_or_past_exhausted):
                    body_doc: mdls.Document = dc.get_documents(name="ARS Essay Body")[0]
                    dc.change_reference_doc_of_cookie(body_doc, current_cookie)
                    self.essay_phase = EssayPhase.BODY
                    new_chunk_index: int | None = self._get_new_chunk_index(current_cookie, query)
                    if (not new_chunk_index is None):
                        dc.change_chunk_index_of_cookie(new_chunk_index, current_cookie)
                    else:
                        conclusion_doc: mdls.Document = dc.get_documents(name="ARS Essay Conclusion")[0]
                        dc.change_reference_doc_of_cookie(conclusion_doc, current_cookie)
                        dc.change_chunk_index_of_cookie(0, current_cookie)
                        self.essay_phase = EssayPhase.CONCLUSION
                    return
            case (EssayPhase.BODY):
                if (current_document is None):
                    body_doc: mdls.Document = dc.get_documents(name="ARS Essay Body")[0]
                    dc.change_reference_doc_of_cookie(body_doc, current_cookie)
                    dc.change_chunk_index_of_cookie(0, current_cookie)
                    self.essay_phase = EssayPhase.BODY
                    return

                if (current_or_past_exhausted):
                    new_chunk_index: int | None = self._get_new_chunk_index(current_cookie, query)
                    # means we used up the entire chunk if it is none
                    if (not new_chunk_index is None):
                        dc.change_chunk_index_of_cookie(new_chunk_index, current_cookie)
                    else:
                        conclusion_doc: mdls.Document = dc.get_documents(name="ARS Essay Conclusion")[0]
                        dc.change_reference_doc_of_cookie(conclusion_doc, current_cookie)
                        dc.change_chunk_index_of_cookie(0, current_cookie)
                        self.essay_phase = EssayPhase.CONCLUSION
                    return
            case (EssayPhase.CONCLUSION):
                if (current_document is None):
                    conclusion_doc: mdls.Document = dc.get_documents(name="ARS Essay Conclusion")[0]
                    dc.change_reference_doc_of_cookie(conclusion_doc, current_cookie)
                    dc.change_chunk_index_of_cookie(0, current_cookie)
                    self.essay_phase = EssayPhase.CONCLUSION
                    return

                if (current_or_past_exhausted):
                    dc.change_reference_doc_of_cookie(None, current_cookie)
                    self.essay_phase = EssayPhase.RECOUNT
                    return
            case (_):
                print("we've reached the end of our essay")
                pass

    # check if we should compress the context in a given chat or cookie session
    @database_sync_to_async
    def check_for_context_compression(self, session: mdls.ChatSession | mdls.CookieSession) -> None:
        if (len(session.context) < self.chat_pairs_before_compression):
            return
        
        dc = DataCache(self.consumer.scope["session"])
        if (isinstance(session, mdls.ChatSession)):
            dc.compress_chat_session(session)
        else:
            dc.compress_cookie_session(session)
        
        session.save()
    
    # process the incoming message and return all relevant information
    async def process_message(self, text_data: str) -> dict[str, str | int | bool]:
        message: str = self._get_message(text_data)
        # this the pasts chats and current chats should be chronological
        current_chat, past_chats, current_cookie = await self.get_all_relevant_chats_cookies()
        # search context allows us to check for more nuanced chunks of data
        search_context: str = self._get_context_stringified(past_chats + [current_chat])
        # main context is what we will put in our prompt as the context
        main_context: str = self._get_context_stringified([current_cookie, current_chat]) 
        # update our database if need be (mainly our reference document for our prompt and the used up docs index in the cookie)
        await self._update_db(current_chat, past_chats, current_cookie, search_context + message)

        return {"message": message, 
                "context": main_context, 
                "reference_material": self._get_reference_material(current_cookie),
                "is_new_user": (current_chat.context == list() and main_context == ""),
                "should_greet_user": (len(current_chat.context) == 0)}

    # handles the initialization logic (e.g. greetings or conclusion) when the user first connects
    async def setup(self) -> None:
        current_chat, past_chats, current_cookie = await self.get_all_relevant_chats_cookies()
        self.essay_phase = await self._infer_essay_progression(current_cookie, current_chat, past_chats)

        if (self.essay_phase == EssayPhase.THESIS and current_cookie.context == list()):
            await self.cg.generate_introduction_greeting_response()
        elif(self.essay_phase != EssayPhase.RECOUNT): 
            await self.cg.generate_familiar_greeting_response()
        else:
            await self.cg.generate_concluding_response()
            self.concluding_statement_made = True

    # wrapper for all the response processing and generation
    async def update(self, text_data: str) -> None:
        processed_msg: dict[str, str | int | bool] = await self.process_message(text_data)

        # this chunk here is to hard cap the response cycle after all the material is exhausted
        if (self.essay_phase == EssayPhase.RECOUNT):

            if (self.concluding_statement_made is False):
                await self.cg.generate_concluding_response()
                self.concluding_statement_made = True
            else:
                await self.cg.generate_secondary_concluding_response()
            return

        subsidiary_documents = await self._get_subsidiary_documents()
        response_outline: ChatOutput = await self.cg.generate_response_outline(processed_msg, subsidiary_documents)

        ws = WebScraper()
        footnotes_information: dict[str, str] = dict()

        for link in response_outline.misc.document_links:
            footnotes_information[link] = await ws.ascrape_playwright(link)

        final_response: dict[str, Any] = await self.cg.generate_response_final(processed_msg, 
                                                                    response_outline.response, 
                                                                    footnotes_information=footnotes_information,
                                                                    image_appendix=subsidiary_documents["image_appendix"])
        await self._store_message_pair(processed_msg["message"], final_response)