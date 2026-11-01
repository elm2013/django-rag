from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase, override_settings

from rag_api.ingestion.indexer import sync_index
from rag_api.models import Document


class FakeCollection:
    """In-memory stand-in for the subset of Chroma used by the indexer."""
    def __init__(self):
        """Initialize an empty collection keyed by vector ID."""
        self.records = {}

    def get(self, where=None, include=None):
        """Return IDs, optionally filtered by the source metadata value."""
        source = where.get('source') if where else None
        ids = [
            item_id for item_id, record in self.records.items()
            if source is None or record['metadata']['source'] == source
        ]
        return {'ids': ids}

    def upsert(self, ids, documents, embeddings, metadatas):
        """Insert or replace records using the supplied parallel sequences."""
        for item_id, document, embedding, metadata in zip(
            ids, documents, embeddings, metadatas,
        ):
            self.records[item_id] = {
                'document': document,
                'embedding': embedding,
                'metadata': metadata,
            }

    def delete(self, ids):
        """Remove records whose IDs are included in ``ids``."""
        for item_id in ids:
            self.records.pop(item_id, None)


class IncrementalIndexTests(TestCase):
    """Verify incremental indexing behavior with isolated local resources."""
    def setUp(self):
        """Create a temporary docs directory and mocked vector services."""
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.docs_path = Path(self.temp_dir.name)
        self.collection = FakeCollection()
        self.patcher = patch(
            'rag_api.ingestion.indexer.get_collection',
            return_value=self.collection,
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.embedding_patcher = patch(
            'rag_api.ingestion.indexer.iter_embedding_batches',
            side_effect=self.fake_embedding_batches,
        )
        self.embedding_mock = self.embedding_patcher.start()
        self.addCleanup(self.embedding_patcher.stop)

    def fake_embedding_batches(self, texts, batch_size=None):
        """Yield deterministic fake vectors for each supplied text."""
        if texts:
            yield 0, [[0.1, 0.2] for _ in texts]

    def run_sync(self):
        """Run synchronization against this test's temporary directory."""
        with override_settings(
            RAG_DOCS_PATH=self.docs_path,
            RAG_CHUNK_SIZE=1000,
            RAG_CHUNK_OVERLAP=100,
            RAG_EMBEDDING_BATCH_SIZE=8,
        ):
            return sync_index()

    def test__sync_index__indexes_new_document_once(self):
        """Verify a new file is indexed once and then skipped as unchanged."""
        guide_path = self.docs_path / 'guide.md'
        guide_path.write_text('first version', encoding='utf-8')

        first_result = self.run_sync()
        second_result = self.run_sync()

        self.assertEqual(first_result['indexed'], 1)
        self.assertEqual(second_result['unchanged'], 1)
        self.assertEqual(self.embedding_mock.call_count, 1)
        document = Document.objects.get(path='guide.md')
        self.assertEqual(document.status, 'indexed')

    def test__sync_index__replaces_changed_document_chunks(self):
        """Verify changed content replaces the previous revision's chunks."""
        path = self.docs_path / 'guide.md'
        path.write_text('first version', encoding='utf-8')
        self.run_sync()
        first_ids = set(self.collection.records)

        path.write_text('second version', encoding='utf-8')
        result = self.run_sync()
        second_ids = set(self.collection.records)

        self.assertEqual(result['indexed'], 1)
        self.assertNotEqual(first_ids, second_ids)
        self.assertEqual(len(second_ids), 1)
        indexed_document = next(iter(self.collection.records.values()))
        self.assertIn('second version', indexed_document['document'])

    def test__sync_index__removes_deleted_document(self):
        """Verify files removed from disk are deleted from both stores."""
        path = self.docs_path / 'guide.md'
        path.write_text('document content', encoding='utf-8')
        self.run_sync()
        path.unlink()

        result = self.run_sync()

        self.assertEqual(result['deleted'], 1)
        self.assertFalse(Document.objects.filter(path='guide.md').exists())
        self.assertFalse(self.collection.records)
