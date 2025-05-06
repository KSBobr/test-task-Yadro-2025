from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models, schemas
from collections import defaultdict
from .utils.graph_validation import validate_dag

def create_graph(db: Session, graph: schemas.GraphCreate):
    try:
        db_graph = models.Graph()
        db.add(db_graph)
        db.commit()
        db.refresh(db_graph)

        # Add nodes
        nodes_map = {}
        for node in graph.nodes:
            db_node = models.Node(name=node.name, graph_id=db_graph.id)
            db.add(db_node)
            nodes_map[node.name] = db_node
        db.commit()

        # Add edges
        for edge in graph.edges:
            db_edge = models.Edge(
                source=edge.source,
                target=edge.target,
                graph_id=db_graph.id
            )
            db.add(db_edge)
        db.commit()

        return {
            "id": db_graph.id,
            "nodes": graph.nodes,
            "edges": graph.edges
        }
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig).split("DETAIL:")[-1].strip()
        raise ValueError(f"Database error: {error_msg}")

def get_graph(db: Session, graph_id: int):
    graph = db.query(models.Graph).filter(models.Graph.id == graph_id).first()
    if not graph:
        return None
    
    nodes = db.query(models.Node).filter(models.Node.graph_id == graph_id).all()
    edges = db.query(models.Edge).filter(models.Edge.graph_id == graph_id).all()
    
    return {
        "id": graph.id,
        "nodes": [{"name": node.name} for node in nodes],
        "edges": [{"source": edge.source, "target": edge.target} for edge in edges]
    }

def get_adjacency_list(db: Session, graph_id: int):
    edges = db.query(models.Edge).filter(models.Edge.graph_id == graph_id).all()
    if not edges:
        return None
    
    adjacency = defaultdict(list)
    for edge in edges:
        adjacency[edge.source].append(edge.target)
    return adjacency

def get_reverse_adjacency_list(db: Session, graph_id: int):
    edges = db.query(models.Edge).filter(models.Edge.graph_id == graph_id).all()
    if not edges:
        return None
    
    reverse_adjacency = defaultdict(list)
    for edge in edges:
        reverse_adjacency[edge.target].append(edge.source)
    return reverse_adjacency

def delete_node(db: Session, graph_id: int, node_name: str):
    # Delete related edges
    db.query(models.Edge).filter(
        (models.Edge.graph_id == graph_id) &
        ((models.Edge.source == node_name) | 
         (models.Edge.target == node_name))
    ).delete(synchronize_session=False)
    
    # Delete node
    deleted_count = db.query(models.Node).filter(
        (models.Node.graph_id == graph_id) &
        (models.Node.name == node_name)
    ).delete(synchronize_session=False)
    
    db.commit()
    return deleted_count > 0