
from functools import lru_cache

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import BASE_DIR


VECTOR_STORE_PATH = BASE_DIR / "data" / "vector_store"

# FAISS cosine-like relevance score threshold.
# Higher score means more relevant.
MIN_RELEVANCE_SCORE = 0.45

DEFAULT_TOP_K = 5


@lru_cache(maxsize=1)
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        ),
        model_kwargs={"device": "cpu"},
        encode_kwargs={
            "normalize_embeddings": True
        },
    )


def vector_store_exists():
    return (
        (VECTOR_STORE_PATH / "index.faiss").exists()
        and (VECTOR_STORE_PATH / "index.pkl").exists()
    )


def load_vector_store():
    if not vector_store_exists():
        return None

    # Only load FAISS indexes created locally
    # by this trusted application.
    return FAISS.load_local(
        str(VECTOR_STORE_PATH),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def add_documents(documents):
    if not documents:
        raise ValueError("No chunks to index.")

    embeddings = get_embeddings()
    store = load_vector_store()

    if store is None:
        store = FAISS.from_documents(
            documents,
            embeddings,
        )
    else:
        store.add_documents(documents)

    VECTOR_STORE_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    store.save_local(str(VECTOR_STORE_PATH))

    return len(documents)


def search_relevant_documents(
    query,
    top_k=DEFAULT_TOP_K,
    min_score=MIN_RELEVANCE_SCORE,
):
    """
    Search FAISS and return documents that meet
    a minimum relevance threshold.

    Returns:
        [
            {
                "document": Document,
                "score": float
            }
        ]
    """
    if not query or not query.strip():
        return []

    store = load_vector_store()

    if store is None:
        return []

    # LangChain FAISS returns L2 distances by default.
    # Lower distance means better match.
    results = store.similarity_search_with_score(
        query,
        k=top_k,
    )

    relevant = []

    for document, distance in results:
        # Normalized embeddings:
        # cosine similarity = 1 - squared_L2 / 2
        similarity = 1.0 - float(distance) / 2.0

        if similarity >= min_score:
            relevant.append(
                {
                    "document": document,
                    "score": round(similarity, 4),
                }
            )

    return relevant
