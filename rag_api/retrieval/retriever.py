from rag_api.embeddings.model import create_embeddings_in_batches
from rag_api.vector_store.chroma import get_collection


def retrieve_documents(question, top_k=4):
    """Retrieve the nearest indexed chunks for a question embedding.

    Args:
        question: Query text to embed and search for.
        top_k: Maximum number of nearest chunks to return.

    Returns:
        list[dict]: Retrieved chunk text, source path, and Chroma distance.
            Returns an empty list when the collection contains no vectors.

    Note:
        The distance is the vector-store distance, not a calibrated
        probability or relevance percentage.
    """
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []

    query_embedding = create_embeddings_in_batches([question])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        include=['documents', 'metadatas', 'distances'],
    )

    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0]

    return [
        {
            'text': document,
            'source': metadata.get('source', 'unknown'),
            'distance': distance,
        }
        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        )
    ]
