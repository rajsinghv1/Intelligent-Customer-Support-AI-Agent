
from functools import lru_cache

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import BASE_DIR


VECTOR_STORE_PATH = (
    BASE_DIR / "data" / "vector_store"
)


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
        and
        (VECTOR_STORE_PATH / "index.pkl").exists()
    )


def load_vector_store():
    if not vector_store_exists():
        return None

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
