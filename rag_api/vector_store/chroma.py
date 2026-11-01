from functools import lru_cache

import chromadb
from django.conf import settings


@lru_cache(maxsize=1)
def get_chroma_client():
    """Return the process-cached persistent Chroma client.

    The database directory is selected by the ``RAG_CHROMA_PATH`` setting.

    Returns:
        chromadb.PersistentClient: Client connected to the local database.
    """
    return chromadb.PersistentClient(path=str(settings.RAG_CHROMA_PATH))


def get_collection():
    """Get or create the configured cosine-distance collection.

    Returns:
        Collection: Chroma collection used for document chunks.
    """
    return get_chroma_client().get_or_create_collection(
        name=settings.RAG_CHROMA_COLLECTION,
        metadata={'hnsw:space': 'cosine'},
    )
