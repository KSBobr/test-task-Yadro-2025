from pydantic import BaseModel, constr
from typing import Dict, List

class NodeBase(BaseModel):
        name: constr( max_length=255, pattern=r'^[a-zA-Z]+$')
class EdgeBase(BaseModel):
    source: str
    target: str

class GraphCreate(BaseModel):
    nodes: List[NodeBase]
    edges: List[EdgeBase]

class GraphCreateResponse(BaseModel):
    id: int

class GraphReadResponse(GraphCreateResponse):
    nodes: List[NodeBase]
    edges: List[EdgeBase]

class AdjacencyListResponse(BaseModel):
    adjacency_list: Dict[str, List[str]]

class ErrorResponse(BaseModel):
    message: str

class HTTPValidationError(BaseModel):
    detail: List[Dict[str, str]]