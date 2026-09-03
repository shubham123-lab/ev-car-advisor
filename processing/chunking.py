from langchain_text_splitters import RecursiveCharacterTextSplitter
from load_data import load_all_documents

def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    chunks = splitter.split_documents(documents)
    return chunks

if __name__ == "__main__":
    docs = load_all_documents()
    chunks = chunk_documents(docs)
    
    print(f"\nOriginal documents: {len(docs)}")
    print(f"After chunking: {len(chunks)}")
    
    # Kitne documents split hue vs as-is rahe, dekhte hain
    print("\nSample chunk:")
    print("Content:", chunks[0].page_content[:200])
    print("Metadata:", chunks[0].metadata)