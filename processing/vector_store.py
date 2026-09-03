from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from chunking import chunk_documents
from load_data import load_all_documents
from dotenv import load_dotenv
import os

load_dotenv()

def build_vector_store():
    print("Documents load ho rahe hain...")
    docs = load_all_documents()
    
    print("\nChunking ho raha hai...")
    chunks = chunk_documents(docs)
    print(f"Total chunks: {len(chunks)}")
    
    print("\nEmbeddings model set ho raha hai...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    print("Vector store ban raha hai (isme time lagega, 1773 chunks hain)...")
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    print("Saving to disk...")
    vector_store.save_local("../data/faiss_index")
    
    print("Done! Vector store save ho gaya.")
    return vector_store

if __name__ == "__main__":
    build_vector_store()