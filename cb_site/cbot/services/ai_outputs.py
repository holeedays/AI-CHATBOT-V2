from pydantic import BaseModel, Field


# structured JSON schemas for our ai API outputs

# this JSON schema works for google and openai's API

# Information regarding response metrics
class MetaData(BaseModel):
    prompt_token_count: int = Field(description="Token usage from user input")
    response_token_count: int = Field(description="Token usage for the prompt")
    total_token_count: int = Field(description="Total token usage, prompt/response token count inclusive")
    timestamp: float = Field(description="Time of this response in unix format")

# other sub-important and important stuff
class Miscellaneous(BaseModel):
    context_exhausted: bool = Field(description="Whether you've exahausted all topics based on the current context")
    document_links: list[str] = Field(description="""Any observed document links (e.g. in footnotes) that were used 
                                      in the response ordered in respect to their chronological order in the response. 
                                      If there are no links, just leave an empty list""")
    image_links: list[str] = Field(description="""Any observed image links (e.g. direct image urls) that were used 
                                      in the response ordered in respect to their chronological order in the response. 
                                      If there are no links, just leave an empty list""")

# the output we are putting out
class ChatOutput(BaseModel):
    # base response fields
    response: str = Field(description="The response")
    misc: Miscellaneous
    metadata: MetaData 

