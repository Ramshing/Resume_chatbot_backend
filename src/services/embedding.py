from langchain_community.embeddings import HuggingFaceEmbeddings
import numpy as np

#Initialize once (global)
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def get_embedding(texts):
    if isinstance(texts, str):
        texts = [texts]

    embeddings = embedding_model.embed_documents(texts)

    #Convert to list
    return [list(e) for e in embeddings]


def get_query_embedding(text):
    emb = embedding_model.embed_query(text)
    return list(emb)   #convert to list
