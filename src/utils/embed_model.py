from langchain_community.embeddings import HuggingFaceEmbeddings

model = None

def get_model():
    global model
    if model is None:
        model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return model