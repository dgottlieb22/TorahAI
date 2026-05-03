from pydantic import BaseModel


class SearchResult(BaseModel):
    ref: str
    hebrew: str
    english: str
    score: float
    explanation: str


SearchResponse = list[SearchResult]
