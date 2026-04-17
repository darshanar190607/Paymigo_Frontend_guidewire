import os
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

# Configuration
INDEX_PATH = "paymigo_assistant/backend/rag/index/faiss_index.bin"
CHUNKS_PATH = "paymigo_assistant/backend/rag/index/chunks.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"

class Retriever:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        if os.path.exists(INDEX_PATH):
            self.index = faiss.read_index(INDEX_PATH)
            with open(CHUNKS_PATH, "rb") as f:
                self.chunks = pickle.load(f)
        else:
            self.index = None
            self.chunks = []
            print(f"Warning: Index not found at {INDEX_PATH}. Please run ingest.py first.")

    def search(self, query, k=3):
        if not self.index:
            return []
        
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding).astype("float32"), k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.chunks):
                results.append(self.chunks[idx])
        
        return results

if __name__ == "__main__":
    # Test retrieval
    retriever = Retriever()
    query = "What are the subscription plans?"
    context = retriever.search(query)
    print(f"Query: {query}")
    print("Context found:")
    for c in context:
        print(f"- {c[:100]}...")
