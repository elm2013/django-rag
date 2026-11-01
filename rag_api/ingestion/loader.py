from pathlib import Path

from django.conf import settings


SUPPORTED_EXTENSIONS = {'.md', '.txt'}


def discover_documents():
    """Find supported document files recursively under the configured root.

    Returns:
        list[Path]: Sorted paths for regular Markdown and plain-text files.
            An absent document directory produces an empty list.
    """
    root = Path(settings.RAG_DOCS_PATH)
    if not root.exists():
        return []

    return sorted(
        path for path in root.rglob('*')
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def load_document(path):
    """Read a UTF-8 encoded document from disk.

    Args:
        path: Filesystem path to the document.

    Returns:
        str: Complete decoded file content.

    Raises:
        OSError: If the file cannot be read.
        UnicodeDecodeError: If the file is not valid UTF-8.
    """
    return path.read_text(encoding='utf-8')
