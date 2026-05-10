from langchain_community.embeddings import HuggingFaceEmbeddings
import numpy as np
from src.utils.embed_model import get_model


#Initialize once (global)
embedding_model = get_model()

def get_embedding(texts):
    if isinstance(texts, str):
        texts = [texts]

    embeddings = embedding_model.embed_documents(texts)

    #Convert to list
    return [list(e) for e in embeddings]


def get_query_embedding(text):
    emb = embedding_model.embed_query(text)
    return list(emb)   #convert to list
