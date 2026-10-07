import os
import random
import uuid
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()

_root = Path(__file__).resolve().parents[1]
qdrant_url = os.getenv("QDRANT_URL", "").strip()
client = QdrantClient(url=qdrant_url) if qdrant_url else QdrantClient(path=str(_root / ".runtime" / "qdrant"))
collection_name = os.getenv("COLLECTION_NAME", "knowledge_base")
model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

if not client.collection_exists(collection_name=collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))

def retrieve_from_store(question: str, user_id:str, n_points: int = 3) -> str:
    results = client.query_points(
        collection_name=collection_name,
        query=models.Document(text=question, model=model_name),
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="group_id",
                    match=models.MatchValue(
                        value=user_id,
                    ),
                )
            ]
        ),
        limit=n_points,
    )
    return results.points

def remove_data_from_store(user_id:str) -> str:
    client.delete(
        collection_name=collection_name,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="group_id",
                        match=models.MatchValue(
                            value=user_id,
                        ),
                    )
                ]
            )
        )
    ) 

def rag_pipeline_setup(user_id, documents):
    client.upsert(
    collection_name=collection_name,
    points=[
        models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{user_id}:{document['chunk_hash']}")),
            vector=models.Document(text=document["page_content"], model=model_name),
            payload={"group_id": user_id, "document": document},
        )
        for idx, document in enumerate(documents)
    ],)
