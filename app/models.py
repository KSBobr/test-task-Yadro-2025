from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from .database import Base

class Graph(Base):
    __tablename__ = "graphs"
    id = Column(Integer, primary_key=True, index=True)

class Node(Base):
    __tablename__ = "nodes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    graph_id = Column(Integer, ForeignKey("graphs.id"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('name', 'graph_id', name='uq_node_graph'),
    )

class Edge(Base):
    __tablename__ = "edges"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(255), nullable=False)
    target = Column(String(255), nullable=False)
    graph_id = Column(Integer, ForeignKey("graphs.id"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('source', 'target', 'graph_id', name='uq_edge_graph'),
    )