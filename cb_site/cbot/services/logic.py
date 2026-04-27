from google import genai
import openai
from openai.types.responses.response_stream_event import ResponseStreamEvent

import os
import re
from typing import Any, Generator
from partialjson import JSONParser

# our container for the output of the model
from .ai_outputs import StructuredOutput

from dotenv import load_dotenv
load_dotenv(".env")


class CB():
    # maybe model specification

    # might use a hybrid of models --
        # gemini for context compression b/c of large scale token window and multimodal capabilities (free)
        # gpt for standard reasoning and user interactions(paid)
    
    def __init__(self, 
                 gemini_model: str = "gemini-3.1-flash-lite-preview", 
                 openai_model: str = "gpt-5.4-nano",
                 embedding_model: str = "text-embedding-3-small",
                 context: list[dict[str, Any]] | None = None) -> None:
        self._setup_apis()
        self._setup_variables(gemini_model, openai_model, embedding_model, context)
    
    def _setup_apis(self) -> None:
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    def _setup_variables(self, 
                         gemini_model: str, 
                         openai_model: str, 
                         embedding_model: str, 
                         context: list[dict[str, Any]] | None) -> None:
        # setup our global variables

        # token counts and context storage (CONTEXT STORAGE ONLY TEMPORARY)
        self.context: list[dict[str, Any]] = context if not context is None else []
        self.context_size_limit: int = 5000

        # models
        self.gemini_model = gemini_model
        self.openai_model = openai_model
        self.embedding_model = embedding_model
        
    # bools we can use later for model identification
    def is_openai_model(self, model: str) -> bool:
        regex: str = r"(?i)gpt"
        return not re.match(regex, model) is None
    
    def is_gemini_model(self, model: str) -> bool:
        regex: str = r"(?i)gemini"
        return not re.match(regex, model) is None
    
    # our context is ordered in a complicated JSON format with metadata and other misc information included
    # but in the case of context compression we only need the raw text, this function does this
    def extract_context_to_str(self) -> str:

        # helper function to extract our context into a string format for the model to read
        context_str: str = ""
        for item in self.context:
            if (item["role"] == "user"):
                context_str += f"User: {item['content']}\n"
            elif (item["role"] == "system"):
                context_str += f"System: {item['content']['response']}\n"
        
        return context_str


    # compress our context
    def get_compressed_context(self, model: str) -> list[dict[str, Any]]:

        if (self.context == []):
            raise Exception("Context is empty, cannot be compressed; please remove this method or relocate")

        # get all raw text of context
        context_str = self.extract_context_to_str()
        # initial prompt instructions
        prompt: str = f"""
                        Please compress the existing context given here: {context_str}.
                        Make sure to keep all the essential points mentioned and 
                        any unique details.
                    """
        # check whether model being used is gemini or openai
        if (self.is_openai_model(model)):
            try:
                response = self.generate_response_openai(model, prompt)
                # essentially refresh our context with the summarized one
                if (not response is None):
                    self.context = [{
                                    "role": "system", 
                                    "content": response.model_dump()
                                    }] 
                else:
                    print("The openai API yielded an error, so it returned None. Keeping the previous context instead.")
            except Exception as e:
                print(f"An error occurred while calling the openai API: {e}. Keeping the previous context instead.")

        elif (self.is_gemini_model(model)):
            try:
                response = self.generate_response_gemini(model, prompt)
                # same for gemini though only if the response is not None, or else just send the previous context
                if (not response is None):
                    self.context = [{
                                    "role": "system", 
                                    "content": response.model_dump()
                                    }] 
                else:
                    print("Something went wrong with the gemini API. Response was None. Keeping the previous context instead.")
            except Exception as e:
                print(f"An error occurred while calling the gemini API: {e}. Keeping the previous context instead.")

        # if an openai model or gemini model isn't used, automatically throw an error
        else:
            raise Exception("This model isn't a openai or gemini model, please use a valid one")
        
        # return the summarized context or unaltered context
        return self.context

    # boiler plater method for generating a reponse from the openai api
    def generate_response_openai(self, model: str, prompt: str) -> StructuredOutput | None:
        response = self.openai_client.responses.parse( 
            model=model,
            input= [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ],
            # this should be the JSON schema specifier
            text_format=StructuredOutput 
        )
        # since we specified a JSON schema, we should access the output through the .output_parsed attribute
        # since the response (sdk) object is exactly the same regardless, the only difference is the
        # output is replaced with out schema; same goes for gemini and im asumming other APIs
        response.output_parsed

        return response.output_parsed
    
    # sends response as multiple chunks, provides more dyanmic feedback
    # Generator type is as follows [yieldtype, sendtype, returntype]
    def generate_response_stream_openai(self, 
                                        model: str, 
                                        prompt: str) -> Generator[ResponseStreamEvent, None, None]:
        # openai is a bit differnt that google with streaming (and documentation too :/)
        # the response stream obj is a response manager class that is not directly iterable
        # however it has __enter__() and exit__() methods meaning it can be accessed by the with-as statement block 
        # (also called context manager), from there we can iterate the response stream object as in gemini's case
        with self.openai_client.responses.stream(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ],
            text_format=StructuredOutput,
        ) as response_stream:
            for chunk in response_stream:
                yield chunk
    
    # similar boiler plate method for gemini
    def generate_response_gemini(self, model: str, prompt: str) -> StructuredOutput | None:
        response = self.google_client.models.generate_content( #type: ignore
            model=model,
            contents=prompt,
            config= {
                "response_mime_type": "application/json",
                "response_json_schema": StructuredOutput.model_json_schema()
            }
        )
        
        if (not response.text is None):
            return StructuredOutput.model_validate_json(response.text)
        
        return None
    
    # Same response stream with gemini
    def generate_response_stream_gemini(self, 
                                        model: str, 
                                        prompt: str) -> Generator[genai.types.GenerateContentResponse, None, None]:

        response_stream = self.google_client.models.generate_content_stream( #type: ignore
            model=model,
            contents=prompt,
            config= {
                "response_mime_type": "application/json",
                "response_json_schema": StructuredOutput.model_json_schema()
            }        
        )

        for chunk in response_stream:
            yield chunk

    def is_last_chunk_gemini(self, chunk: genai.types.GenerateContentResponse) -> bool:
        return not chunk.candidates[0].finish_reason is None #type: ignore

    def is_last_chunk_openai(self, chunk: ResponseStreamEvent) -> bool:
        return chunk.type == "response.completed" # type: ignore

        
# if __name__ == "__main__":
#     cb = CB()
#     cb.gemini_model = "gemini-2.5-flash-lite"
#     chunks: genai.types.GenerateContentResponse = genai.types.GenerateContentResponse()
#     jparser = JSONParser()
#     accumulated_response = ""

#     for chunk in cb.generate_response_stream_gemini(cb.gemini_model, "Write me a short sad store sad story"):
#         try:
#             accumulated_response += chunk.candidates[0].content.parts[0].text #type: ignore
#         except:
#             pass
        
#         if (accumulated_response is None):
#             break

#         print(jparser.parse(accumulated_response)) #type: ignore

    # for chunk in cb.generate_response_stream_openai(cb.openai_model, "Write me a short sad story"):
    #     try:
    #         # print(jparser.parse(chunk.snapshot)) #type: ignore
    #         print(chunk.type)
    #     except:
    #         pass

    
