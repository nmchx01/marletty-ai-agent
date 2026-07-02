import sys
from pathlib import Path
from typing import List


# Permite ejecutar este archivo directamente con:
# python backend/agent/rag.py "pregunta"
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))


from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from backend.agent.embeddings import SafeGoogleEmbeddings
from backend.core.config import get_settings


VECTOR_STORE_DIR = get_settings().vector_store_dir

DEFAULT_TOP_K = 3

_vector_store = None


def load_environment() -> None:
    """Carga variables de entorno necesarias para embeddings."""
    get_settings().require_google_api_key()


def validate_vector_store_exists() -> None:
    """Verifica que el vector store FAISS exista en disco."""

    index_faiss = VECTOR_STORE_DIR / "index.faiss"
    index_pkl = VECTOR_STORE_DIR / "index.pkl"

    if not VECTOR_STORE_DIR.exists():
        raise FileNotFoundError(
            f"No existe la carpeta del vector store: {VECTOR_STORE_DIR}. "
            "Primero ejecuta: python backend/agent/loader.py"
        )

    if not index_faiss.exists() or not index_pkl.exists():
        raise FileNotFoundError(
            "No se encontró un índice FAISS válido. "
            "Primero ejecuta: python backend/agent/loader.py"
        )


def get_vector_store() -> FAISS:
    """
    Carga el vector store FAISS desde disco.

    Se mantiene en memoria después de la primera carga para evitar
    recargarlo en cada pregunta.
    """

    global _vector_store

    if _vector_store is not None:
        return _vector_store

    load_environment()
    validate_vector_store_exists()

    embeddings = SafeGoogleEmbeddings()

    _vector_store = FAISS.load_local(
        str(VECTOR_STORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )

    return _vector_store


def search_relevant_documents(query: str, top_k: int = DEFAULT_TOP_K) -> List[Document]:
    """Busca los documentos más relevantes para una consulta."""

    clean_query = query.strip()

    if not clean_query:
        return []

    vector_store = get_vector_store()

    return vector_store.similarity_search(clean_query, k=top_k)


def format_document_for_context(document: Document, index: int) -> str:
    """Convierte un Document en texto listo para el prompt."""

    metadata = document.metadata or {}

    source = metadata.get("source", "fuente desconocida")
    document_type = metadata.get("type", "documento")
    page = metadata.get("page")

    page_label = f", página {page}" if page else ""

    return (
        f"[Fuente {index}: {source} ({document_type}{page_label})]\n"
        f"{document.page_content.strip()}"
    )


def get_relevant_context(query: str, top_k: int = DEFAULT_TOP_K) -> str:
    """
    Recupera y formatea el contexto relevante para el LLM.

    Este texto será insertado después en el system prompt blindado.
    """

    documents = search_relevant_documents(query=query, top_k=top_k)

    if not documents:
        return "No se encontró contexto relevante en los documentos."

    formatted_documents = [
        format_document_for_context(document, index)
        for index, document in enumerate(documents, start=1)
    ]

    return "\n\n---\n\n".join(formatted_documents)


def debug_search(query: str) -> None:
    """Permite probar el RAG desde terminal."""

    print("🔎 Consulta:")
    print(query)
    print()

    print(f"📚 Recuperando top {DEFAULT_TOP_K} chunks...")
    context = get_relevant_context(query)

    print()
    print("✅ Contexto recuperado:")
    print("=" * 80)
    print(context)
    print("=" * 80)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print('Uso: python backend/agent/rag.py "¿Dónde están ubicados?"')
        raise SystemExit(1)

    user_query = " ".join(sys.argv[1:])
    debug_search(user_query)
