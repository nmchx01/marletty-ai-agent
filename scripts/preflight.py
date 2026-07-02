import importlib
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"

REQUIRED_FILES = [
    BASE_DIR / "backend" / "main.py",
    BASE_DIR / "backend" / "agent" / "loader.py",
    BASE_DIR / "backend" / "agent" / "rag.py",
    BASE_DIR / "backend" / "agent" / "llm.py",
    BASE_DIR / "backend" / "agent" / "prompts.py",
    BASE_DIR / "backend" / "agent" / "sanitizer.py",
    BASE_DIR / "backend" / "agent" / "cache.py",
    BASE_DIR / "backend" / "agent" / "embeddings.py",
    BASE_DIR / "frontend" / "index.html",
    BASE_DIR / "frontend" / "css" / "styles.css",
    BASE_DIR / "frontend" / "js" / "chat.js",
    BASE_DIR / "requirements.txt",
    BASE_DIR / ".env.example",
    BASE_DIR / ".gitignore",
]

REQUIRED_IMPORTS = [
    "fastapi",
    "uvicorn",
    "dotenv",
    "faiss",
    "pypdf",
    "langchain_groq",
    "langchain_google_genai",
    "langchain_community",
    "langchain_text_splitters",
]

REQUIRED_ENV_VARS = [
    "GROQ_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_EMBEDDING_MODEL",
]


def print_ok(message: str) -> None:
    print(f"✅ {message}")


def print_fail(message: str) -> None:
    print(f"❌ {message}")


def check_files() -> bool:
    print("\n📁 Revisando archivos base...")

    success = True

    for file_path in REQUIRED_FILES:
        if file_path.exists():
            print_ok(str(file_path.relative_to(BASE_DIR)))
        else:
            print_fail(f"Falta {file_path.relative_to(BASE_DIR)}")
            success = False

    return success


def check_imports() -> bool:
    print("\n📦 Revisando imports principales...")

    success = True

    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
            print_ok(module_name)
        except Exception as error:
            print_fail(f"{module_name}: {error}")
            success = False

    return success


def check_env() -> bool:
    print("\n🔐 Revisando variables de entorno...")

    load_dotenv(ENV_PATH)

    success = True

    if not ENV_PATH.exists():
        print_fail("No existe archivo .env en la raíz del proyecto.")
        return False

    print_ok(".env encontrado")

    for var_name in REQUIRED_ENV_VARS:
        value = os.getenv(var_name)

        if value:
            print_ok(var_name)
        else:
            print_fail(f"Falta {var_name}")
            success = False

    return success


def check_vector_store() -> bool:
    print("\n🧠 Revisando vector store FAISS...")

    vector_store_dir = BASE_DIR / "backend" / "vector_store"
    index_faiss = vector_store_dir / "index.faiss"
    index_pkl = vector_store_dir / "index.pkl"

    if index_faiss.exists() and index_pkl.exists():
        print_ok("FAISS listo: index.faiss + index.pkl")
        return True

    print_fail("No se encontró FAISS completo. Ejecuta: python backend/agent/loader.py")
    return False


def check_docs() -> bool:
    print("\n📄 Revisando documentos RAG...")

    docs_dir = BASE_DIR / "backend" / "docs"

    if not docs_dir.exists():
        print_fail("No existe backend/docs/")
        return False

    docs = list(docs_dir.glob("*.txt")) + list(docs_dir.glob("*.pdf"))

    if docs:
        print_ok(f"Documentos encontrados: {len(docs)}")
        return True

    print_fail("No hay documentos .txt o .pdf en backend/docs/")
    return False


def main() -> None:
    print("🚀 Preflight — Marletty AI Agent")

    checks = [
        check_files(),
        check_imports(),
        check_env(),
        check_docs(),
        check_vector_store(),
    ]

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if all(checks):
        print("🎉 Proyecto listo para producción/deploy.")
        raise SystemExit(0)

    print("⚠️ Hay pendientes antes del deploy.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()