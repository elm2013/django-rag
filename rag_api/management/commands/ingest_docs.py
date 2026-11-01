from django.core.management.base import BaseCommand, CommandError

from rag_api.ingestion.indexer import sync_index


class Command(BaseCommand):
    """Run incremental synchronization of the local RAG document index."""
    help = 'Incrementally synchronize the RAG index with local documents.'

    def handle(self, *args, **options):
        """Execute indexing and report synchronization statistics.

        Raises:
            CommandError: If synchronization fails globally or any individual
                document could not be indexed or deleted.
        """
        try:
            result = sync_index()
        except Exception as exc:
            message = 'Index synchronization failed: {}'.format(exc)
            raise CommandError(message) from exc

        self.stdout.write(
            'Indexed: {indexed}, unchanged: {unchanged}, '
            'deleted: {deleted}, chunks processed: {chunks}, '
            'failed: {failed}.'.format(**result)
        )

        for error in result['errors']:
            self.stderr.write(self.style.ERROR(error))

        if result['failed']:
            raise CommandError('Some documents could not be synchronized.')

        message = 'Index synchronization complete.'
        self.stdout.write(self.style.SUCCESS(message))
