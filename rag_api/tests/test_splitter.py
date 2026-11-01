from django.test import SimpleTestCase

from rag_api.ingestion.splitter import split_text


class SplitTextTests(SimpleTestCase):
    """Test chunk boundaries and validation in the text splitter."""
    def test__split_text__returns_empty_list_for_empty_text(self):
        """Return no chunks when the input text is empty."""
        self.assertEqual(split_text(''), [])

    def test__split_text__keeps_all_content(self):
        """Keep the beginning and ending content across generated chunks."""
        text = 'alpha beta gamma delta epsilon'
        chunks = split_text(text, chunk_size=12, overlap=3)

        self.assertTrue(chunks)
        self.assertIn('alpha', chunks[0])
        self.assertTrue(any('epsilon' in chunk for chunk in chunks))

    def test__split_text__rejects_invalid_overlap(self):
        """Reject overlap values that are not smaller than chunk size."""
        with self.assertRaises(ValueError):
            split_text('some text', chunk_size=10, overlap=10)
