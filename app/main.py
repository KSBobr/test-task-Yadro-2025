from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .database import SessionLocal, engine
from . import models, schemas, crud
from .utils.graph_validation import validate_dag
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def validate_node_name(name: str):
    if not isinstance(name, str):
        raise ValueError("Node name must be a string")
    
    if len(name) == 0:
        raise ValueError("Node name cannot be empty")
    
    if len(name) > 255:
        raise ValueError("Node name exceeds maximum length (255 chars)")
    
    if not re.fullmatch(r'^[a-zA-Z]+$', name):
        raise ValueError("Node name must contain only latin letters (A-Z, a-z)")
    
def check_for_duplicate_edges(edges: list[schemas.EdgeBase]):
    edge_pairs = set()
    duplicates = set()
    
    for edge in edges:
        edge_pair = (edge.source, edge.target)
        if edge_pair in edge_pairs:
            duplicates.add(f"{edge.source}->{edge.target}")
        edge_pairs.add(edge_pair)
    
    if duplicates:
        raise ValueError(f"Duplicate edges detected: {', '.join(duplicates)}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/api/graph/", 
         response_model=schemas.GraphCreateResponse,
         status_code=status.HTTP_201_CREATED)
def create_graph(graph: schemas.GraphCreate, db: Session = Depends(get_db)):
    try:
        for node in graph.nodes:
            validate_node_name(node.name)

        # Проверка уникальности имен
        node_names = [node.name for node in graph.nodes]
        if len(node_names) != len(set(node_names)):
            raise ValueError("Duplicate node names detected")

        check_for_duplicate_edges(graph.edges)
        existing_node_names = set(node_names)
        for edge in graph.edges:
            if edge.source not in existing_node_names:
                raise ValueError(f"Source node '{edge.source}' not found in nodes list")
            if edge.target not in existing_node_names:
                raise ValueError(f"Target node '{edge.target}' not found in nodes list")

        nodes_data = [{"name": n.name} for n in graph.nodes]
        edges_data = [{"source": e.source, "target": e.target} for e in graph.edges]
        
        if not validate_dag(nodes_data, edges_data):
            raise ValueError("Graph contains cycles")

        return crud.create_graph(db, graph)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/api/graph/{graph_id}/", response_model=schemas.GraphReadResponse)
def read_graph(graph_id: int, db: Session = Depends(get_db)):
    db_graph = crud.get_graph(db, graph_id)
    if not db_graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    return db_graph

@app.get("/api/graph/{graph_id}/adjacency_list", 
        response_model=schemas.AdjacencyListResponse)
def get_adjacency_list(graph_id: int, db: Session = Depends(get_db)):
    adjacency = crud.get_adjacency_list(db, graph_id)
    if adjacency is None:
        raise HTTPException(status_code=404, detail="Graph not found")
    return {"adjacency_list": adjacency}

@app.get("/api/graph/{graph_id}/reverse_adjacency_list",
        response_model=schemas.AdjacencyListResponse)
def get_reverse_adjacency_list(graph_id: int, db: Session = Depends(get_db)):
    reverse_adjacency = crud.get_reverse_adjacency_list(db, graph_id)
    if reverse_adjacency is None:
        raise HTTPException(status_code=404, detail="Graph not found")
    return {"adjacency_list": reverse_adjacency}

@app.delete("/api/graph/{graph_id}/node/{node_name}", 
          status_code=status.HTTP_204_NO_CONTENT)
def delete_node(
    graph_id: int,
    node_name: str,
    db: Session = Depends(get_db)
):
    if not crud.delete_node(db, graph_id, node_name):
        raise HTTPException(status_code=404, detail="Node not found")
    return {}

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    logger.error(f"Database integrity error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"message": "Database integrity error"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )
