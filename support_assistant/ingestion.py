import os
import glob
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "C:/Users/Sushma Bhattu/Desktop/SushmaBhattu-Zeptos-data-capstone-project/support_assistant/chroma_db"
COLLECTION_NAME = "zepto_policies"
DOCS_DIR = "C:/Users/Sushma Bhattu/Desktop/SushmaBhattu-Zeptos-data-capstone-project/support_assistant/docs"

def initialize_vector_store():
    # Setup ChromaDB with local sentence-transformer embedding model
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, 
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Check if database is already populated
    if collection.count() > 0:
        return collection

    doc_files = sorted(glob.glob(os.path.join(DOCS_DIR, "doc_*.txt")))
    
    documents = []
    ids = []
    metadatas = []

    for filepath in doc_files:
        doc_id = os.path.basename(filepath).replace(".txt", "")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            documents.append(content)
            ids.append(f"{doc_id}_chunk1")
            metadatas.append({"source_doc": doc_id})

    if documents:
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
    
    return collection

if __name__ == "__main__":
    coll = initialize_vector_store()
    print(f"Successfully ingested {coll.count()} document chunks into ChromaDB.")