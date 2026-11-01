import hashlib
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from rag_api.embeddings.model import iter_embedding_batches
from rag_api.ingestion.loader import discover_documents, load_document
from rag_api.ingestion.splitter import split_text
from rag_api.models import Document
from rag_api.vector_store.chroma import get_collection


def sha256_text(text):
    """Return the SHA-256 hexadecimal digest of a text value.

    Args:
        text: Unicode text whose content should be fingerprinted.

    Returns:
        str: A 64-character hexadecimal digest.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _document_chunk_ids(collection, source):
    """Fetch vector IDs belonging to one source document.

    Args:
        collection: Chroma collection containing document chunks.
        source: Relative path stored in each chunk's ``source`` metadata.

    Returns:
        list: IDs of all chunks associated with the source.
    """
    """Return IDs for one source document, not the whole collection."""
    result = collection.get(where={'source': source}, include=[])
    return result.get('ids', [])


def _remove_obsolete_chunks(collection, source, current_ids):
    """Delete stored chunks for a source that are not in the new revision.

    Args:
        collection: Chroma collection to update.
        source: Relative path identifying the source document.
        current_ids: IDs generated for the revision being indexed.

    Note:
        Chroma deletion is not transactional. If deletion fails partway
        through, some chunks from the previous revision may already be gone.
    """
    current_ids = set(current_ids)
    existing_ids = _document_chunk_ids(collection, source)
    obsolete_ids = [
        item_id for item_id in existing_ids
        if item_id not in current_ids
    ]
    if obsolete_ids:
        collection.delete(ids=obsolete_ids)


def _index_document(path, relative_path, document, collection):
    """Index a new or changed file, leaving unchanged files untouched.

    New chunk IDs include the content hash, so revisions have distinct IDs.
    The new vectors are upserted in batches before obsolete IDs are removed.
    Vector-store writes and the Django metadata save are separate operations;
    they cannot be committed or rolled back as one transaction.

    Args:
        path: Absolute path to the source file.
        relative_path: Stable path relative to ``RAG_DOCS_PATH``.
        document: Existing Document row, or ``None`` for a new file.
        collection: Chroma collection used to store chunk vectors.

    Returns:
        tuple: An action name (``indexed`` or ``unchanged``) and chunk count.

    Raises:
        Exception: Propagates file, embedding, Chroma, or database errors to
            the caller so the synchronization process can record the failure.
    """
    content = load_document(path)
    content_hash = sha256_text(content)

    if (
        document
        and document.status == Document.Status.INDEXED
        and document.sha256 == content_hash
    ):
        return 'unchanged', 0

    chunks = split_text(
        content,
        chunk_size=settings.RAG_CHUNK_SIZE,
        overlap=settings.RAG_CHUNK_OVERLAP,
    )

    # Include the content hash in IDs. New vectors are written before old
    # vectors are removed, so a failed update preserves the last index.
    current_ids = []
    inserted_ids = []

    try:
        for start, embeddings in iter_embedding_batches(
            chunks,
            batch_size=settings.RAG_EMBEDDING_BATCH_SIZE,
        ):
            batch_chunks = chunks[start:start + len(embeddings)]
            batch_ids = [
                '{}:{}:{}'.format(relative_path, content_hash, index)
                for index in range(start, start + len(batch_chunks))
            ]
            metadatas = [
                {
                    'source': relative_path,
                    'content_hash': content_hash,
                    'chunk_index': index,
                }
                for index in range(start, start + len(batch_chunks))
            ]
            collection.upsert(
                ids=batch_ids,
                documents=batch_chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            current_ids.extend(batch_ids)
            inserted_ids.extend(batch_ids)

        # Remove previous revisions only after all new batches are stored.
        _remove_obsolete_chunks(collection, relative_path, current_ids)

    except Exception:
        # Remove partial writes and preserve the previous revision.
        if inserted_ids:
            collection.delete(ids=inserted_ids)
        raise

    if document is None:
        document = Document(path=relative_path)

    document.sha256 = content_hash
    document.chunk_count = len(chunks)
    document.status = Document.Status.INDEXED
    document.last_indexed_at = timezone.now()
    document.error_message = ''
    document.save()

    return 'indexed', len(chunks)


def sync_index():
    """Synchronize the Chroma index with supported files on disk.

    New and changed files are embedded; unchanged files are skipped; vectors
    and metadata rows for files no longer present are removed. Per-file errors
    are collected so that other files can still be processed.

    The Chroma collection must be dedicated to this RAG application because
    cleanup is scoped by the ``source`` metadata field. Run only one
    synchronization process at a time; concurrent runs are not coordinated.

    Returns:
        dict: Counts for indexed, unchanged, deleted, processed chunks, and
        failed documents, plus an ``errors`` list containing failure details.
    """
    """Index only new/changed files and remove chunks for deleted files.

    The Chroma collection must be dedicated to this RAG application because
    cleanup is scoped by the `source` metadata field.
    """
    docs_root = Path(settings.RAG_DOCS_PATH)
    paths = discover_documents()
    collection = get_collection()

    seen_paths = set()
    stats = {
        'indexed': 0,
        'unchanged': 0,
        'deleted': 0,
        'chunks': 0,
        'failed': 0,
    }
    errors = []

    for path in paths:
        relative_path = str(path.relative_to(docs_root))
        seen_paths.add(relative_path)
        document = Document.objects.filter(path=relative_path).first()

        try:
            action, chunk_count = _index_document(
                path,
                relative_path,
                document,
                collection,
            )
            stats[action] += 1
            stats['chunks'] += chunk_count
        except Exception as exc:
            stats['failed'] += 1
            errors.append('{}: {}'.format(relative_path, exc))
            if document is None:
                document = Document(path=relative_path)
            document.status = Document.Status.FAILED
            document.error_message = str(exc)[:4000]
            document.save()

    # Only files absent from the current filesystem scan are deleted. This is
    # scoped per source, avoiding collection.get() over every vector record.
    stale_documents = Document.objects.exclude(path__in=seen_paths)
    for document in stale_documents.iterator():
        try:
            stale_ids = _document_chunk_ids(collection, document.path)
            if stale_ids:
                collection.delete(ids=stale_ids)
            document.delete()
            stats['deleted'] += 1
        except Exception as exc:
            stats['failed'] += 1
            errors.append('{} (delete): {}'.format(document.path, exc))

    stats['errors'] = errors
    return stats
