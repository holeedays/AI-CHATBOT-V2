from pydantic import BaseModel, Field


# this JSON schema works for google and openai's API
class StructuredOutput(BaseModel):
    # base response fields
    response: str = Field(description="The response")
    prompt_token_count: int = Field(description="Token usage from user input")
    response_token_count: int = Field(description="Token usage for the prompt")
    total_token_count: int = Field(description="Total token usage, prompt/response token count inclusive")
    timestamp: float = Field(description="Time of this response in unix format")

    # specifically for our document, since we want the model to iterate through our entire essay
    source_document_chunk: str = Field(description="The source document chunk that this response is based on")
