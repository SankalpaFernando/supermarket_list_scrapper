import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key)
index_name = "products"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(index_name)

model = SentenceTransformer('all-MiniLM-L6-v2')

print("Connected to Supabase and Pinecone successfully!")
