from functools import lru_cache

from django.conf import settings
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model():
    """Return the process-cached sentence-transformer embedding model.

    Returns:
        SentenceTransformer: The model configured by ``RAG_EMBEDDING_MODEL``.
    """
    return SentenceTransformer(settings.RAG_EMBEDDING_MODEL)


def iter_embedding_batches(texts, batch_size=None):
    """Yield normalized embeddings for consecutive batches of input texts.

    Args:
        texts: Sequence of strings to encode.
        batch_size: Maximum number of texts per batch. Defaults to the
            ``RAG_EMBEDDING_BATCH_SIZE`` setting.

    Yields:
        tuple: The starting offset and a list of embedding vectors.

    Raises:
        ValueError: If the effective batch size is not positive.
    """
    """Yield embeddings by batch without retaining all vectors in memory."""
    if not texts:
        return

    batch_size = batch_size or settings.RAG_EMBEDDING_BATCH_SIZE
    if batch_size <= 0:
        raise ValueError('batch_size must be greater than zero.')

    model = get_embedding_model()
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        embeddings = model.encode(
            batch,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        yield start, embeddings.tolist()


def create_embeddings_in_batches(texts, batch_size=None):
    """Encode texts and collect all resulting vectors in memory.

    Prefer ``iter_embedding_batches`` when processing large collections.

    Args:
        texts: Sequence of strings to encode.
        batch_size: Maximum number of texts per encoding batch.

    Returns:
        list: Embedding vectors in the same order as the input texts.
    """
    """Return all embeddings; prefer the iterator for large inputs."""
    return [
        embedding
        for _, batch in iter_embedding_batches(texts, batch_size)
        for embedding in batch
    ]
