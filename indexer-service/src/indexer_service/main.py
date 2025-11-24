from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import uuid

app = FastAPI()

# Configuration
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))
COLLECTION_NAME = "code_context"
MODEL_NAME = "all-MiniLM-L6-v2"

# Initialize Model and Client
# We use a global variable for the model to load it once
model = None
client = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
    return model

def get_client():
    global client
    if client is None:
        # Check if we should use in-memory for testing
        if os.environ.get("QDRANT_LOCATION") == ":memory:":
             client = QdrantClient(location=":memory:")
        else:
             client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return client

class SearchQuery(BaseModel):
    query: str
    limit: int = 5

class IndexRequest(BaseModel):
    texts: List[str]
    metadatas: Optional[List[Dict[str, Any]]] = None

@app.on_event("startup")
def startup_event():
    # Load model and connect to Qdrant
    get_model()
    q_client = get_client()

    # Create collection if it doesn't exist
    if not q_client.collection_exists(COLLECTION_NAME):
        q_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

@app.get("/")
def read_root():
    return {"message": "Indexer Service"}

@app.get("/health")
def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {"status": "ok"}

@app.post("/index")
def index_documents(request: IndexRequest):
    embeddings = get_model().encode(request.texts)
    points = []
    for i, (text, embedding) in enumerate(zip(request.texts, embeddings)):
        metadata = request.metadatas[i] if request.metadatas else {}
        metadata["text"] = text
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding.tolist(),
            payload=metadata
        ))

    get_client().upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    return {"status": "success", "count": len(points)}

@app.post("/search")
def search(query: SearchQuery):
    embedding = get_model().encode(query.query).tolist()

    # Use query_points instead of search as search seems to be missing in this environment/version combination
    # query_points is the newer API unified for search/recommend/etc.
    # Note: query_points returns QueryResponse which might have points inside it or be a list of ScoredPoint

    results = get_client().query_points(
        collection_name=COLLECTION_NAME,
        query=embedding, # In newer client versions, 'query' argument takes the vector
        limit=query.limit
    ).points

    return {"results": [
        {"score": hit.score, "payload": hit.payload}
        for hit in results
    ]}
