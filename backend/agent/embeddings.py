from typing import List

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.core.config import get_settings


class SafeGoogleEmbeddings(Embeddings):
    """
    Wrapper seguro para embeddings de Google.

    Algunas versiones/modelos de Gemini devuelven un solo embedding cuando
    reciben una lista de textos. Para FAISS necesitamos exactamente un embedding
    por cada documento, por eso procesamos los textos uno por uno.
    """

    def __init__(self) -> None:
        settings = get_settings()

        kwargs = {
            "model": settings.google_embedding_model,
        }

        if settings.google_embedding_dimension:
            kwargs["output_dimensionality"] = settings.google_embedding_dimension

        self.client = GoogleGenerativeAIEmbeddings(**kwargs)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera un embedding por cada documento."""

        embeddings = []

        for index, text in enumerate(texts, start=1):
            clean_text = text.strip()

            if not clean_text:
                clean_text = "Documento vacío."

            print(f"   Embedding {index}/{len(texts)}")

            embedding = self.client.embed_query(clean_text)
            embeddings.append(embedding)

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Genera embedding para una consulta del usuario."""

        clean_text = text.strip() if text and text.strip() else "Consulta vacía."

        return self.client.embed_query(clean_text)
