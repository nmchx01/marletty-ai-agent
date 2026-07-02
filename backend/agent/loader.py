import os
import sys
import tempfile
from pathlib import Path
from typing import List


# Permite ejecutar este archivo directamente con:
# python backend/agent/loader.py
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))


from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from pypdf import PdfReader

from backend.agent.embeddings import SafeGoogleEmbeddings
from backend.core.config import get_settings


# Rutas principales del proyecto.
SETTINGS = get_settings()
DOCS_DIR = SETTINGS.docs_dir
VECTOR_STORE_DIR = SETTINGS.vector_store_dir

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

SUPPORTED_EXTENSIONS = [".txt", ".pdf"]


def load_environment() -> None:
    """Carga variables de entorno desde el archivo .env."""

    SETTINGS.require_google_api_key()

def get_embedding_model() -> SafeGoogleEmbeddings:
    """Crea el modelo seguro de embeddings de Google."""

    return SafeGoogleEmbeddings()


def get_source_files() -> List[Path]:
    """Obtiene todos los archivos TXT y PDF de backend/docs."""

    if not DOCS_DIR.exists():
        raise FileNotFoundError(
            f"No existe la carpeta de documentos: {DOCS_DIR}. "
            "Crea backend/docs/ y agrega archivos .txt o .pdf."
        )

    source_files = []

    for extension in SUPPORTED_EXTENSIONS:
        source_files.extend(DOCS_DIR.glob(f"*{extension}"))

    source_files = sorted(source_files)

    if not source_files:
        raise FileNotFoundError(
            f"No se encontraron documentos en {DOCS_DIR}. "
            "Agrega al menos un archivo .txt o .pdf antes de generar el vector store."
        )

    return source_files


def read_txt_file(txt_path: Path) -> str:
    """
    Lee un archivo TXT.

    Primero intenta con UTF-8. Si el archivo viene con otra codificación,
    usa latin-1 como respaldo para evitar que el loader se caiga.
    """

    try:
        return txt_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return txt_path.read_text(encoding="latin-1")


def extract_documents_from_txt(txt_path: Path) -> List[Document]:
    """
    Convierte un archivo TXT en un Document de LangChain.

    Cada TXT se trata como una fuente completa. El chunking se hace después.
    """

    text = read_txt_file(txt_path).strip()

    if not text:
        return []

    return [
        Document(
            page_content=text,
            metadata={
                "source": txt_path.name,
                "type": "txt",
            },
        )
    ]


def extract_documents_from_pdf(pdf_path: Path) -> List[Document]:
    """
    Extrae texto página por página desde un PDF.

    Cada página se convierte en un Document con metadata para saber
    de qué archivo y página viene cada fragmento.
    """

    documents = []

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as error:
        raise RuntimeError(f"No se pudo leer el PDF {pdf_path.name}: {error}") from error

    for page_index, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""

        clean_text = page_text.strip()

        if not clean_text:
            continue

        documents.append(
            Document(
                page_content=clean_text,
                metadata={
                    "source": pdf_path.name,
                    "type": "pdf",
                    "page": page_index,
                },
            )
        )

    return documents


def extract_documents_from_file(file_path: Path) -> List[Document]:
    """Extrae documentos según el tipo de archivo."""

    extension = file_path.suffix.lower()

    if extension == ".txt":
        return extract_documents_from_txt(file_path)

    if extension == ".pdf":
        return extract_documents_from_pdf(file_path)

    return []


def load_all_documents() -> List[Document]:
    """Carga todos los documentos TXT/PDF y retorna una lista de Documents."""

    source_files = get_source_files()
    all_documents = []

    print(f"📄 Documentos encontrados: {len(source_files)}")

    for file_path in source_files:
        print(f"   Leyendo: {file_path.name}")

        file_documents = extract_documents_from_file(file_path)
        all_documents.extend(file_documents)

        print(f"   Documentos extraídos: {len(file_documents)}")

    if not all_documents:
        raise RuntimeError(
            "Los archivos fueron encontrados, pero no se pudo extraer texto. "
            "Verifica que los TXT no estén vacíos o que los PDF no sean imágenes escaneadas."
        )

    return all_documents


def split_documents(documents: List[Document]) -> List[Document]:
    """Divide los documentos en chunks pequeños para RAG."""

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)

    if not chunks:
        raise RuntimeError("No se generaron chunks a partir de los documentos.")

    return chunks


def build_and_save_vector_store(chunks: List[Document]) -> None:
    """Genera FAISS en temporal y reemplaza el índice solo al completarse."""

    embeddings = get_embedding_model()

    print("🧠 Generando embeddings con Google...")
    vector_store = FAISS.from_documents(chunks, embeddings)

    print(f"💾 Guardando FAISS en: {VECTOR_STORE_DIR}")
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="marletty-faiss-", dir=VECTOR_STORE_DIR.parent
    ) as temp_dir:
        temp_path = Path(temp_dir)
        vector_store.save_local(str(temp_path))
        for filename in ("index.faiss", "index.pkl"):
            os.replace(temp_path / filename, VECTOR_STORE_DIR / filename)


def main() -> None:
    """Ejecuta el pipeline completo de carga de documentos."""

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("🚀 Iniciando generación del vector store de Marletty...")

    load_environment()

    documents = load_all_documents()
    print(f"✅ Documentos cargados: {len(documents)}")

    chunks = split_documents(documents)
    print(f"✅ Chunks generados: {len(chunks)}")

    build_and_save_vector_store(chunks)

    print("🎉 Vector store generado correctamente.")
    print(f"📁 Archivos guardados en: {VECTOR_STORE_DIR}")


if __name__ == "__main__":
    main()
