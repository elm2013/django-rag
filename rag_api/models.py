from django.db import models


class Document(models.Model):
    """Track the indexing state and content fingerprint of a source file.

    The row stores document-level metadata only; chunk text and embeddings
    are stored separately in Chroma.
    """
    class Status(models.TextChoices):
        """Lifecycle states recorded by the document indexer."""
        PENDING = 'pending', 'Pending'
        INDEXED = 'indexed', 'Indexed'
        FAILED = 'failed', 'Failed'

    path = models.CharField(max_length=1024, unique=True)
    sha256 = models.CharField(max_length=64, blank=True)
    chunk_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    last_indexed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Define the default ordering for document records."""
        ordering = ['path']

    def __str__(self):
        """Return the document's path as its human-readable identifier."""
        return self.path
