import json 
import re
from pathlib import Path 

import ollama 
import pymupdf

from config import EMBEDDING_MODEL

BASE_DIR = Path(__file__).resolve().parent.parent 

DOCUMENTS_DIR = BASE_DIR / "documents"
RAG_DATA_DIR = BASE_DIR / "rag_data"
INDEX_FILE = RAG_DATA_DIR / "index.json"

CHUNK_SIZE = 250
CHUNK_OVERLAP = 50
EMBEDDING_BATCH_SIZE = 32

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def chunk_text(
    text, 
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP
):
    if overlap >= chunk_size:
        raise ValueError(
            "L'overlap doit être inférieur à chunk_size."
        )
    
    words = text.split()
    
    chunks = []
    
    start = 0
    
    while start < len(words):
        end = min(
            start + chunk_size,
            len(words)
        )
        
        chunk = " ".join(
            words[start:end]
        ).strip()
        
        if chunk:
            chunks.append(chunk)
        
        if end == len(words):
            break 
        
        start = end - overlap 
        
    return chunks 

def extract_chunks_from_pdf(pdf_path):
    chunks = []
    
    with pymupdf.open(pdf_path) as document:
        
        for page_index, page in enumerate(
            document, 
            start=1 
        ):
            text = page.get_text("text")
            
            text = clean_text(text)
            
            if not text:
                continue 
            
            page_chunks = chunk_text(text)
            
            for chunk_index, chunk in enumerate(
                page_chunks, 
                start=1 
            ): 
                chunks.append(
                    {
                        "source": str(
                            pdf_path.relative_to(
                                DOCUMENTS_DIR
                            )
                        ),
                        "page": page_index,
                        "chunk": chunk_index,
                        "text": chunk
                    }
                )
                
    return chunks

def embed_chunks(chunks):
    texts = [
        chunk["text"]
        for chunk in chunks 
    ]
    
    embeddings = []
    
    total = len(texts)
    
    for start in range(
        0, 
        total, 
        EMBEDDING_BATCH_SIZE
    ):
        batch = texts[
            start:start + EMBEDDING_BATCH_SIZE
        ]
        
        print(
            f"Embeddings : "
            f"{start + 1}-"
            f"{min(start + len(batch), total)}"
            f"/{total}"
        )
        
        response = ollama.embed(
            model=EMBEDDING_MODEL,
            input=batch 
        )
        
        embeddings.extend(
            response["embeddings"]
        )
    
    for chunk, embedding in zip(
        chunks, 
        embeddings
    ):
        chunk["embedding"] = embedding
        
    return chunks

def build_index():
    DOCUMENTS_DIR.mkdir(
        parents=True, 
        exist_ok=True 
    )
    
    pdf_files = sorted(
        DOCUMENTS_DIR.rglob("*.pdf")
    )
    
    if not pdf_files:
        print(
            "Aucun PDF trouvé dans documents/."
        )
        return 
    
    all_chunks = []
    
    print(
        f"{len(pdf_files)} PDF trouvé(s).\n"
    )
    
    for pdf_path in pdf_files:
        
        print(
            f"Lecture : "
            f"{pdf_path.relative_to(DOCUMENTS_DIR)}"
        )
        
        chunks = extract_chunks_from_pdf(pdf_path)
        
        print(f" -> {len(chunks)} chunks")
        
        all_chunks.extend(chunks)
        
    if not all_chunks:
        print(
            "Aucun texte exploitable trouvé."
        )
        return 
    
    print(
        f"\nTotal : {len(all_chunks)} chunks"
    )
    
    print(
        f"Modèle : {EMBEDDING_MODEL}\n"
    )

    all_chunks = embed_chunks(
        all_chunks
    )

    RAG_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    data = {
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "chunks": all_chunks
    }

    with INDEX_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False
        )

    print(
        "\nIndex créé : "
        f"{INDEX_FILE}"
    )

    print(
        f"{len(all_chunks)} passages indexés."
    )
    
if __name__ == "__main__":
    build_index()