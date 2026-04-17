import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

# Configuration
KNOWLEDGE_FILE = "paymigo_assistant/backend/rag/knowledge.txt"
INDEX_PATH = "paymigo_assistant/backend/rag/index/faiss_index.bin"
CHUNKS_PATH = "paymigo_assistant/backend/rag/index/chunks.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"

def load_and_chunk(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Simple chunking by double newlines (sections)
    chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
    return chunks

def ingest():
    print("Starting ingestion...")
    chunks = load_and_chunk(KNOWLEDGE_FILE)
    if not chunks:
        return

    print(f"Loaded {len(chunks)} chunks.")
    
    # Initialize model
    model = SentenceTransformer(MODEL_NAME)
    
    # Generate embeddings
    embeddings = model.encode(chunks)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype("float32"))
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    
    # Save index and chunks
    faiss.write_index(index, INDEX_PATH)
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)
    
    print(f"Successfully ingested {len(chunks)} chunks into {INDEX_PATH}")

if __name__ == "__main__":
    ingest()
