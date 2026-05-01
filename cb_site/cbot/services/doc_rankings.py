from google import genai
import openai
from openai.types import CreateEmbeddingResponse

import bm25s
from bm25s.tokenization import Tokenized

from .api_logic import ApiLogic

import numpy as np
import os

# from dotenv import load_dotenv
# load_dotenv(".env")

# logic regarding ranking documents (in the case of retrieval)
class DocRanker():
    def __init__(self, 
                 embedding_model: str = "gemini-embedding-001"
                 ) -> None:
        self.embedding_model = embedding_model
        self._setup_apis()

    def _setup_apis(self) -> None:
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    ################################################################################# ranking methods

    # order relevant documents scored based on keywords and word frequency 
    def order_relevant_docs_bm25(self, corpus: str | list[str], query: str, unordered: bool = False) -> list[tuple[str, float]]:
        # tokenizing and indexing our document body
        corpus_tokens: list[list[str]] | Tokenized = bm25s.tokenize(corpus) #type: ignore
        retriever: bm25s.BM25 = bm25s.BM25(corpus=corpus)
        retriever.index(corpus_tokens) #type: ignore

        # tokenizing our query and checking it against the corpus body
        query_tokens: list[list[str]] | Tokenized = bm25s.tokenize(query) #type: ignore
        docs, score = retriever.retrieve(query_tokens, k=len(corpus))

        # we're gonna normalize the scores
        max_score: float = max(score[0])

        corpus_graded: list[tuple[str, float]] = [(d, s/max_score) for d,s in zip(docs[0], score[0])]


        # hash mapping if we want the original segment of docs 
        # by the way, type() and isinstance() cannot suppot generic types like list[str]; they only support running types
        # like list; the generic types are just a way for static checkers like pylance or mypy to enforce types
        if (unordered is True and type(corpus) is list):
            corpus_dict: dict[str, float] = dict()
            for d, s in zip(docs[0], score[0]): 
                corpus_dict[d] = s

            for i in range(len(corpus)):
                corpus_graded[i] = (corpus[i], corpus_dict[corpus[i]]/max_score)

        return corpus_graded
    
    # order relevant documents scored based on semantic vector embedding
    def order_relevant_docs_RAG(self, corpus: str | list[str], query: str, unordered: bool = False):
        scores: list[float] = list()

        # weird thing with open ai is their embedding models don't have GPT in the name, so we'll check like this
        if (ApiLogic.is_gemini_model(self.embedding_model)):
            query_embed_gemini: genai.types.EmbedContentResponse = self.get_embeddings_gemini(self.embedding_model, query, "RETRIEVAL_QUERY")
            corpus_embed_gemini: genai.types.EmbedContentResponse = self.get_embeddings_gemini(self.embedding_model, corpus, "RETRIEVAL_DOCUMENT")

            query_vector: np.ndarray = np.array(query_embed_gemini.embeddings[0].values)  #type: ignore
            scores = [self.cos_similarity(query_vector, np.array(embedding.values)) #type: ignore
                      for embedding in corpus_embed_gemini.embeddings] #type: ignore
        else:
            query_embed_openai: CreateEmbeddingResponse = self.get_embeddings_openai(self.embedding_model, query)
            corpus_embed_openai: CreateEmbeddingResponse = self.get_embeddings_openai(self.embedding_model, corpus)

            query_vector: np.ndarray = np.array(query_embed_openai.data[0].embedding) 
            scores = [self.cos_similarity(query_vector, np.array(embedding.embedding)) 
                      for embedding in corpus_embed_openai.data]
        
        corpus_graded: list[tuple[str, float]] = [(doc, score) for doc, score in zip(corpus, scores)]

        if (unordered is True):
            return corpus_graded
        else:
            return sorted(corpus_graded, key=lambda item: item[1], reverse=True)
        
    # hybrid method that joins all our other retrieving methods together (Reciprocal Rank Fusion (RRF))
    def order_relevant_docs_RRF(self, corpus: str | list[str], query: str, k: int = 60, unordered: bool = False) -> list[tuple[str, float]]:
        # our other retrieval methods
        sparse_scores: list[tuple[str, float]] = self.order_relevant_docs_bm25(corpus, query, False) # from bm25
        dense_scores: list[tuple[str, float]] = self.order_relevant_docs_RAG(corpus, query, False) # from our vector embedding (RAG)
        # convert them to hashmaps and include only their ranks (the only important chunk of our rrf)
        sparse_rank: dict[str,int]= {doc:rank for rank, (doc, _) in enumerate(sparse_scores, start=1)}
        dense_rank: dict[str,int]= {doc:rank for rank, (doc, _) in enumerate(dense_scores, start=1)}
        # get all unique documents 
        all_docs: set[str] = set(sparse_rank) 
        all_docs.update(dense_rank)

        corpus_graded: list[tuple[str, float]] = list()
        # now calculate the rrf score 
        for doc in all_docs:
            rrf_score: float = 0

            if (doc in sparse_rank):
                rrf_score += 1/(k+sparse_rank[doc])
            
            if (doc in dense_rank):
                rrf_score += 1/(k+dense_rank[doc])
            
            corpus_graded.append((doc, rrf_score))

        # note the docs and score might not be exactly the same since we converted it to a set 

        if (unordered is True):
            return corpus_graded
        else:
            return sorted(corpus_graded, key=lambda item: item[1], reverse=True)
        
    ################################################################################# misc methods

    # cos similarity eqn; range -1 to 1
    @classmethod
    def cos_similarity(cls, vector_a: np.ndarray, vector_b: np.ndarray) -> float:
        if (np.linalg.norm(vector_a) == 0 or np.linalg.norm(vector_b) == 0):
            return 0
        
        return np.dot(vector_a, vector_b) / (np.linalg.norm(vector_a) * np.linalg.norm(vector_b))
    
    # embedding methods for each model
    def get_embeddings_gemini(self, model: str, input: str | list[str], task_type: str) -> genai.types.EmbedContentResponse:
        embeddings: genai.types.EmbedContentResponse = self.google_client.models.embed_content( #type: ignore
                model=model,
                contents=input, 
                config=genai.types.EmbedContentConfig(task_type=task_type)
        )

        return embeddings

    def get_embeddings_openai(self, model: str, input: str | list[str]) -> CreateEmbeddingResponse:
        embeddings: CreateEmbeddingResponse = self.openai_client.embeddings.create(
            input=input,
            model=model
        )

        return embeddings

# corpus = [
#     "The cat jumped over the landing",
#     "The sandwich ate the fat ass chicken",
#     "The man did the swiss cheese louiston",
#     "Aunt jerimiah would've been proud"
# ]
# dc = DocRanker()
# print(dc.order_relevant_docs_RRF(corpus, "What did the cat do with aunt jerimiah?", unordered=True))
