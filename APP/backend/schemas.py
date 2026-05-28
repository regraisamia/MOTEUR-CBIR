from typing import List, Optional
from pydantic import BaseModel


class Metadata(BaseModel):
    image_name: str
    patient_id: Optional[str]
    sex: Optional[str]
    age_approx: Optional[float]
    anatom_site: Optional[str]
    diagnosis: Optional[str]
    benign_malignant: Optional[str]
    target: int


class SearchResult(BaseModel):
    rank: int
    image_id: str
    image_url: str
    label: int
    label_name: str
    distance: float
    similarity: float
    metadata: Metadata


class SearchResponse(BaseModel):
    query_info: dict
    method: str
    search_time_ms: float
    top_k: int
    results: List[SearchResult]
