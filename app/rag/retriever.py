
from app.rag.vector_store import load_vector_store


def retrieve_documents(query, top_k=4):
    if not query.strip():
        return []

    store = load_vector_store()

    if store is None:
        return []

    results = store.similarity_search(
        query,
        k=top_k,
    )

    return results
